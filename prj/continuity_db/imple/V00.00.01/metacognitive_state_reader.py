from __future__ import annotations

# R1.1: Read the metacognitive state table so wave 1 can observe current goal and focus.
import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB = Path("continuity.db")


def fetch_metacognitive_state(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT state_key, category, value, confidence, provenance, version, updated_at
        FROM metacognitive_state
        ORDER BY state_key
        """
    ).fetchall()
    return [
        {
            "state_key": state_key,
            "category": category,
            "value": value,
            "confidence": confidence,
            "provenance": provenance,
            "version": version,
            "updated_at": updated_at,
        }
        for state_key, category, value, confidence, provenance, version, updated_at in rows
    ]


def summarize_metacognitive_state(rows: list[dict[str, Any]]) -> str:
    by_key = {row["state_key"]: row for row in rows}
    lines = ["Metacognitive state"]
    goal = by_key.get("primary_goal")
    focus = by_key.get("current_focus")
    lines.append(f"- primary_goal: {goal['value'] if goal else '<missing>'}")
    lines.append(f"- current_focus: {focus['value'] if focus else '<missing>'}")
    lines.append(f"- entries: {len(rows)}")
    lines.append("- details:")
    for row in rows:
        lines.append(
            f"  - {row['state_key']} [{row['category']}] v{row['version']} "
            f"confidence={row['confidence']}: {row['value']}"
        )
    return "\n".join(lines)


def build_report(db_path: str | Path) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    try:
        rows = fetch_metacognitive_state(conn)
    finally:
        conn.close()
    return {
        "db": str(db_path),
        "table": "metacognitive_state",
        "count": len(rows),
        "rows": rows,
        "summary": summarize_metacognitive_state(rows),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read and summarize continuity.db metacognitive_state.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = build_report(args.db)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    else:
        print(report["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
