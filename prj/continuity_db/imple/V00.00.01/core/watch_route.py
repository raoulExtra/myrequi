#!/usr/bin/env python3
"""Watch input patterns: poll latest chat message and trigger routes based on plain text matching."""

import argparse
import hashlib
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[5]
DB_PATH = ROOT / "continuity.db"


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    ensure_trigger_schema(con)
    return con


def ensure_trigger_schema(con: sqlite3.Connection) -> None:
    """Ensure watch trigger table has generic dedupe fields."""
    con.execute("""
        CREATE TABLE IF NOT EXISTS trigger_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_type TEXT NOT NULL CHECK(trigger_type IN ('input', 'state', 'time')),
            condition_spec TEXT NOT NULL,
            action_route_name TEXT NOT NULL,
            action_parameters TEXT,
            enabled INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_triggered TEXT,
            last_trigger_signature TEXT
        )
    """)
    try:
        con.execute("ALTER TABLE trigger_patterns ADD COLUMN last_trigger_signature TEXT")
    except sqlite3.OperationalError:
        pass
    con.commit()


def _trigger_signature(row: sqlite3.Row, latest_text: str) -> str:
    """Stable signature for this watch rule against the currently latest text."""
    payload = "\0".join([
        str(row["id"]),
        row["condition_spec"] or "",
        row["action_route_name"] or "",
        row["action_parameters"] or "",
        latest_text or "",
    ])
    return hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()


def add_watch(con: sqlite3.Connection, text: str, route: str, routearg: str = "") -> None:
    ensure_trigger_schema(con)
    con.execute(
        "INSERT OR IGNORE INTO trigger_patterns (trigger_type, condition_spec, action_route_name, action_parameters, enabled) VALUES (?, ?, ?, ?, ?)",
        ("input", text, route, routearg, 1),
    )
    con.commit()


def _extract_groups(pattern: str, text: str) -> dict[str, Any]:
    """Extract regex groups from routearg when it already matches a route pattern."""
    import re

    params: dict[str, Any] = {"input_text": text}
    if not pattern or not text:
        return params
    try:
        match = re.match(pattern, text, re.IGNORECASE)
    except re.error:
        return params
    if not match:
        return params
    if match.groups():
        params["groups"] = list(match.groups())
        for idx, value in enumerate(match.groups(), start=1):
            params[f"group{idx}"] = value
    return params


def _decision_for_route(con: sqlite3.Connection, route_name: str, routearg: str) -> Optional[dict[str, Any]]:
    """Build an InputActionRouter decision for a named route without per-route code."""
    row = con.execute(
        "SELECT route_name, input_pattern, command_template, scope FROM control_command_routes WHERE route_name=? AND enabled=1 LIMIT 1",
        (route_name,),
    ).fetchone()
    if row is not None:
        params = _extract_groups(row["input_pattern"], routearg or "")
        if routearg and "group1" not in params:
            params["group1"] = routearg
        return {
            "matched_pattern": "watch_trigger",
            "route_name": row["route_name"],
            "route_type": "control_command",
            "command_template": row["command_template"],
            "input_pattern": row["input_pattern"],
            "parameters": params,
            "priority": 100,
            "description": row["scope"],
        }

    row = con.execute(
        "SELECT route_name, input_pattern, handler, required_capability, output_contract FROM agent_tool_routes WHERE route_name=? AND enabled=1 LIMIT 1",
        (route_name,),
    ).fetchone()
    if row is not None:
        params = _extract_groups(row["input_pattern"], routearg or "")
        if routearg and "group1" not in params:
            params["group1"] = routearg
        return {
            "matched_pattern": "watch_trigger",
            "route_name": row["route_name"],
            "route_type": "agent_tool",
            "handler": row["handler"],
            "required_capability": row["required_capability"],
            "output_contract": row["output_contract"],
            "input_pattern": row["input_pattern"],
            "parameters": params,
            "priority": 100,
            "description": row["output_contract"],
        }

    return None


def _check_once(con: sqlite3.Connection, pi_session: Any, pid: str = None, router: Any = None) -> None:
    """Check current latest chat text against enabled watch patterns once."""
    try:
        text = pi_session.latest_assistant_text(pid=pid) if pid else pi_session.latest_assistant_text()
        if not text:
            return
        ensure_trigger_schema(con)
        for row in con.execute(
            "SELECT id, trigger_type, condition_spec, action_route_name, action_parameters, last_trigger_signature FROM trigger_patterns WHERE enabled=1"
        ):
            if row["condition_spec"] in text:
                signature = _trigger_signature(row, text)
                if row["last_trigger_signature"] == signature:
                    print(f"[watch] skipped repeat for '{row['condition_spec']}' on unchanged latest message")
                    continue
                route_name = row["action_route_name"]
                routearg = row["action_parameters"] or ""
                print(f"[watch] matched '{row['condition_spec']}' -> route={route_name} arg={routearg}")
                decision = _decision_for_route(con, route_name, routearg)
                if decision is None:
                    print(f"[watch] route not found or disabled: {route_name}")
                    continue
                if router is None:
                    from input_action_router import InputActionRouter
                    router = InputActionRouter(DB_PATH, pid=pid)
                result = router.execute_routing_decision(decision, routearg or route_name, pid=pid)
                action_result = result.get("action_result") if isinstance(result, dict) else None
                if isinstance(action_result, dict):
                    output = action_result.get("assistant_text") or action_result.get("value") or action_result.get("result") or action_result.get("status")
                else:
                    output = action_result
                print(f"[watch] route result: {str(output or '')[:500]}")
                con.execute(
                    "UPDATE trigger_patterns SET last_triggered=CURRENT_TIMESTAMP, last_trigger_signature=? WHERE id=?",
                    (signature, row["id"]),
                )
                con.commit()
    except Exception as exc:
        print(f"[watch] check error: {exc}")


def start_watch(con: sqlite3.Connection, sleep: int = 30, pid: str = None, router: Any = None) -> None:
    try:
        import pi_session
    except Exception:
        print("pi_session import failed; cannot fetch chat messages.")
        return

    print(f"[watch] starting loop (interval={sleep}s)")
    # Immediate first check, then the same check in the loop
    _check_once(con, pi_session, pid, router=router)
    while True:
        time.sleep(sleep)
        _check_once(con, pi_session, pid, router=router)


def cmd_init(args) -> None:
    with connect(args.db) as con:
        ensure_trigger_schema(con)
        print(f"initialized trigger_patterns table in {args.db}")


def cmd_add(args) -> None:
    with connect(args.db) as con:
        add_watch(con, args.text, args.route, args.routearg)
        print(f"added watch: text='{args.text}' route={args.route} arg={args.routearg}")


def cmd_start(args) -> None:
    from input_action_router import InputActionRouter

    db_path = Path(args.db)
    router = InputActionRouter(db_path, pid=args.pid)
    start_watch(router.conn, args.sleep, pid=args.pid, router=router)


def main() -> None:
    parser = argparse.ArgumentParser(description="Watch input patterns")
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--pid", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub_init = sub.add_parser("init")
    sub_init.set_defaults(func=cmd_init)
    sub_add = sub.add_parser("add")
    sub_add.add_argument("--text", required=True)
    sub_add.add_argument("--route", required=True)
    sub_add.add_argument("--routearg", default="")
    sub_add.set_defaults(func=cmd_add)
    sub_start = sub.add_parser("start")
    sub_start.add_argument("--pid", default=None)
    sub_start.add_argument("--sleep", type=int, default=30)
    sub_start.set_defaults(func=cmd_start)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()