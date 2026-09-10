#!/usr/bin/env python3
"""Sync active AI model from pi settings into continuity.db.

Each invocation records one (model, session) link in `model_session_link`,
allowing multiple sessions to track different active models concurrently.

Usage:
    python3 store_active_model.py                          # auto-detect session from pi
    python3 store_active_model.py --session-id ID          # explicit session
    python3 store_active_model.py --auto-add               # add model if missing
    python3 store_active_model.py --show                     # show recent session links
    python3 store_active_model.py --end-session             # close current session's link
    python3 store_active_model.py --set-default-model M [--set-default-provider P]
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import uuid
from pathlib import Path

DB = Path(__file__).resolve().parent / "continuity.db"
SETTINGS = Path("/home/peter/.pi/agent/settings.json")
STORE = Path("/home/peter/.pi/agent/models-store.json")
SESSIONS_ROOT = Path("/home/peter/.pi/agent/sessions")


def get_active_model() -> tuple[str, dict | None]:
    settings = json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {}
    model = settings.get("defaultModel", "unknown")
    provider = settings.get("defaultProvider")
    model_info: dict | None = None
    if STORE.exists():
        store = json.loads(STORE.read_text())
        candidates = [model]
        if provider:
            candidates.insert(0, f"{provider}/{model}")
        for _provider, block in store.items():
            if not isinstance(block, dict):
                continue
            for entry in block.get("models", []):
                entry_id = entry.get("id")
                if entry_id in candidates:
                    model_info = entry
                    break
            if model_info:
                break
    return model, model_info


def set_default_model(model: str, provider: str | None = None) -> tuple[str, str | None]:
    """Update ~/.pi/agent/settings.json with a new default model/provider.

    Accepts either:
    - model='openrouter/free' (provider inferred)
    - model='free', provider='openrouter'
    """
    settings = json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {}
    resolved_model = model.strip()
    resolved_provider = provider.strip() if provider and provider.strip() else None

    if "/" in resolved_model and not resolved_provider:
        resolved_provider, resolved_model = resolved_model.split("/", 1)

    settings["defaultModel"] = resolved_model
    if resolved_provider:
        settings["defaultProvider"] = resolved_provider
    SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")
    return resolved_model, resolved_provider


def detect_session_id() -> str:
    """Best-effort detection of the current pi session id.

    Falls back to a short UUID when nothing can be inferred.
    """
    env = os.environ
    for key in ("PI_SESSION_ID", "PI_SESSION", "SESSION_ID"):
        if env.get(key):
            return env[key] or ""
    # Try to find the most recent JSONL in the project session dir
    if SESSIONS_ROOT.exists():
        candidates = sorted(
            SESSIONS_ROOT.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        for c in candidates:
            if not c.name.startswith("--"):
                # The filename pattern is {ISO_T}_{UUID}.jsonl — use the UUID part.
                stem = c.stem
                parts = stem.split("_")
                # Last segment is the UUID
                return parts[-1] if parts else stem
    return f"local-{uuid.uuid4().hex[:8]}"


def ensure_model(cur: sqlite3.Cursor, model: str, info: dict | None) -> str:
    """Make sure the model has rows in object_metadata + ai_model_details.

    Returns one of: 'existed', 'auto_added', 'missing'.
    """
    cur.execute(
        "SELECT object_key FROM object_metadata WHERE object_type='ai_model' AND object_key=?",
        (model,),
    )
    if cur.fetchone():
        return "existed"
    if info is None:
        return "missing"
    tags = json.dumps(
        [
            f"provider:{info.get('provider', 'unknown')}",
            f"context:{info.get('contextWindow', 0)}",
            "tier:active",
        ]
    )
    cur.execute(
        "INSERT INTO object_metadata (object_type, object_key, sensitivity, review_status, tags_json) VALUES (?, ?, ?, ?, ?)",
        ("ai_model", model, "internal", "unreviewed", tags),
    )
    cur.execute(
        "INSERT INTO ai_model_details (model_key, version, architecture, context_window_tokens, training_cutoff, performance_json) VALUES (?, ?, ?, ?, ?, ?)",
        (
            model,
            (info.get("version") if info and info.get("version") else "latest"),
            (info.get("name") if info and info.get("name") else model),
            (info.get("contextWindow") if info and info.get("contextWindow") else None),
            None,
            json.dumps(
                {
                    "cost": info.get("cost") if info else {},
                    "provider": info.get("provider") if info else None,
                    "notes": "Auto-added from settings.json",
                }
            ),
        ),
    )
    return "auto_added"


def sync(
    db_path: str | Path,
    auto_add: bool = False,
    session_id: str | None = None,
) -> tuple[str, str, str]:
    db_path = Path(db_path)
    model, info = get_active_model()
    sid = session_id or detect_session_id()

    con = sqlite3.connect(str(db_path))
    cur = con.cursor()

    model_state = ensure_model(cur, model, info)
    if model_state == "missing":
        if not auto_add:
            con.close()
            print(f"⚠️ Model {model!r} not found in continuity.db and no info to add it.")
            print("   Run with --auto-add, or pre-populate the model.")
            return model, sid, "missing"
        # auto_add but info is None — synthesize minimal row
        cur.execute(
            "INSERT INTO object_metadata (object_type, object_key, sensitivity, review_status, tags_json) VALUES (?, ?, ?, ?, ?)",
            ("ai_model", model, "internal", "unreviewed", "[]"),
        )
        cur.execute(
            "INSERT INTO ai_model_details (model_key, version, architecture, context_window_tokens) VALUES (?, ?, ?, ?)",
            (model, "latest", "Unknown", None),
        )
        model_state = "auto_added"

    # Close any currently-open link for this session
    cur.execute(
        "UPDATE model_session_link SET is_active = 0, ended_at = CURRENT_TIMESTAMP WHERE session_id = ? AND is_active = 1",
        (sid,),
    )

    # Insert new active link for this session
    cur.execute(
        "INSERT INTO model_session_link (model_key, session_id, is_active, context_window_tokens, provider, source_json) VALUES (?, ?, 1, ?, ?, ?)",
        (
            model,
            sid,
            info.get("contextWindow") if info else None,
            info.get("provider") if info else "unknown",
            json.dumps({"settings": str(SETTINGS), "store": str(STORE)}),
        ),
    )

    # Also append a row to the existing single-active-flag history (active_model_state)
    cur.execute(
        "INSERT INTO active_model_state (model_key, model_name, context_window_tokens, provider, source_json, is_active) VALUES (?, ?, ?, ?, ?, 1)",
        (
            model,
            info.get("name") if info else model,
            info.get("contextWindow") if info else None,
            info.get("provider") if info else "unknown",
            json.dumps({"session_id": sid, "settings": str(SETTINGS), "store": str(STORE)}),
        ),
    )

    con.commit()
    con.close()
    print(f"✅ Model {model!r} linked to session {sid!r} (model: {model_state})")
    return model, sid, model_state


def list_active(db_path: str | Path) -> None:
    db_path = Path(db_path)
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    cur.execute(
        """
        SELECT session_id, model_key, provider, context_window_tokens, started_at, ended_at, is_active
        FROM model_session_link
        ORDER BY started_at DESC
        LIMIT 20
        """
    )
    rows = cur.fetchall()
    con.close()
    if not rows:
        print("No model_session_link rows yet.")
        return
    print(f"{'session_id':<36} {'model_key':<28} {'provider':<12} {'ctx':>8} {'started_at':<20} {'ended_at':<20} {'active':<6}")
    print("-" * 130)
    for sid, mk, prov, ctx, st, en, act in rows:
        print(
            f"{(sid or '?'):<36} {mk:<28} {(prov or '?'):<12} {ctx or 0:>8} {st:<20} {(en or '-'):<20} {bool(act)!s:<6}"
        )


def end_session(db_path: str | Path, session_id: str | None = None) -> None:
    db_path = Path(db_path)
    sid = session_id or detect_session_id()
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    cur.execute(
        "UPDATE model_session_link SET is_active = 0, ended_at = CURRENT_TIMESTAMP WHERE session_id = ? AND is_active = 1",
        (sid,),
    )
    con.commit()
    con.close()
    print(f"🛑 Closed active model links for session {sid!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync active AI model into continuity.db")
    parser.add_argument("--db", default=str(DB), help="Path to continuity.db")
    parser.add_argument("--auto-add", action="store_true", help="Auto-add model if missing")
    parser.add_argument("--show", action="store_true", help="List recent model_session_link rows")
    parser.add_argument("--session-id", default=None, help="Override session id (default: auto-detect)")
    parser.add_argument("--end-session", action="store_true", help="Close current session's active link")
    parser.add_argument("--set-default-model", default=None, help="Update ~/.pi/agent/settings.json defaultModel")
    parser.add_argument("--set-default-provider", default=None, help="Optional defaultProvider when setting the default model")
    args = parser.parse_args()

    if args.show:
        list_active(args.db)
        sys.exit(0)
    if args.end_session:
        end_session(args.db, args.session_id)
        sys.exit(0)
    if args.set_default_model:
        model, provider = set_default_model(args.set_default_model, args.set_default_provider)
        print(f"✅ Default model set to {model!r}" + (f" (provider: {provider!r})" if provider else ""))
        sync(args.db, auto_add=args.auto_add, session_id=args.session_id)
        sys.exit(0)

    sync(args.db, auto_add=args.auto_add, session_id=args.session_id)
