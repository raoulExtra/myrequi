#!/usr/bin/env python3
"""Continuously deliver new completed chat messages to active messenger adapters."""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path


PID_PATH = Path("/tmp/myrequi-chat-trace-poll.pid")
CURSOR_PATH = Path("/tmp/myrequi-chat-trace-cursor")


def _text(message: dict) -> str:
    content = message.get("content") or []
    if isinstance(content, str):
        return content.strip()
    return "\n".join(
        part.get("text", "")
        for part in content
        if isinstance(part, dict) and part.get("type") == "text"
    ).strip()


def _auto_delivery_enabled(db_path: Path) -> bool:
    """Read the live delivery switch so the poller responds without restart."""
    try:
        with sqlite3.connect(db_path, timeout=1.0) as conn:
            row = conn.execute(
                "SELECT enabled FROM feature_flags WHERE feature_key='chat_trace_auto' LIMIT 1"
            ).fetchone()
        return bool(row and row[0])
    except sqlite3.Error:
        return False


def run(db_path: Path, pid: str | None, interval: float) -> None:
    core_root = Path(__file__).resolve().parent
    extension_root = core_root.parent / "extension"
    if str(core_root) not in sys.path:
        sys.path.insert(0, str(core_root))
    if str(extension_root) not in sys.path:
        sys.path.insert(0, str(extension_root))
    import pi_session
    from message_adapter_registry import send_to_active_adapters

    PID_PATH.write_text(str(os.getpid()))
    PID_PATH.chmod(0o600)
    cursor = CURSOR_PATH.read_text().strip() if CURSOR_PATH.exists() else ""
    try:
        while True:
            if not _auto_delivery_enabled(db_path):
                break
            history = pi_session.get_session_history(
                pid=pid, limit=500, since=cursor or None,
                event="message_end", max_bytes=20_000_000,
            )
            events = ((history.get("data") or {}).get("events") or [])
            for event in events:
                event_id = str(event.get("id") or event.get("event_id") or event.get("timestamp") or "")
                if event_id and event_id == cursor:
                    continue
                message = event.get("message") or (event.get("data") or {}).get("message") or {}
                if message.get("role") == "assistant":
                    text = _text(message)
                    if text:
                        send_to_active_adapters(db_path, None, text)
                if event_id:
                    cursor = event_id
                    CURSOR_PATH.write_text(cursor)
                    CURSOR_PATH.chmod(0o600)
            time.sleep(interval)
    finally:
        PID_PATH.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--pid", default=None)
    parser.add_argument("--interval", type=float, default=2.0)
    args = parser.parse_args()
    run(args.db, args.pid, args.interval)


if __name__ == "__main__":
    main()
