"""Telegram messenger extension boundary.

The token prompt belongs to the extension, while tests can pass a mock bot
object. This module does not persist the token or contact Telegram.
"""

from __future__ import annotations

import asyncio
from getpass import getpass
import os
import sqlite3
from pathlib import Path
from typing import Any, Callable

import sys



PROJECT_ROOT = Path(__file__).resolve().parents[7]
EXTENSION_ROOT = Path(__file__).resolve().parents[2]
if str(EXTENSION_ROOT) not in sys.path:
    sys.path.insert(0, str(EXTENSION_ROOT))
from extension_state import (  # noqa: E402
    require_extension_ready,
    set_configuration_state,
)

DEFAULT_DB = PROJECT_ROOT / "continuity.db"
ARTIFACT_NAME = "messenger-adapter.telegramm"


async def receive_one_async(bot: Any, offset: int | None = None) -> dict[str, Any]:
    """Receive one pending Telegram update without persisting its message."""
    kwargs = {"limit": 1}
    if offset is not None:
        kwargs["offset"] = offset
    updates = await bot.get_updates(**kwargs)
    if not updates:
        raise LookupError("Telegram getUpdates returned no pending message")
    update = updates[0]
    chat = getattr(getattr(update, "effective_chat", None), "id", None)
    message = getattr(getattr(update, "effective_message", None), "text", None)
    return {
        "update_id": getattr(update, "update_id", None),
        "chat_id": str(chat) if chat is not None else None,
        "text": message,
    }


def receive_one(bot: Any, db_path: str | Path | None = None) -> dict[str, Any]:
    """Expose one update and advance Telegram's offset across CLI invocations."""
    offset = None
    connection = None
    if db_path is not None:
        connection = sqlite3.connect(db_path)
        connection.execute("CREATE TABLE IF NOT EXISTS telegram_runtime_state (state_key TEXT PRIMARY KEY, state_value TEXT NOT NULL)")
        row = connection.execute("SELECT state_value FROM telegram_runtime_state WHERE state_key='next_update_offset'").fetchone()
        offset = int(row[0]) if row else None
    try:
        received = asyncio.run(receive_one_async(bot, offset))
        next_offset = received.get("update_id")
        if connection is not None and next_offset is not None:
            connection.execute(
                "INSERT INTO telegram_runtime_state(state_key,state_value) VALUES('next_update_offset',?) ON CONFLICT(state_key) DO UPDATE SET state_value=excluded.state_value",
                (str(int(next_offset) + 1),),
            )
            connection.commit()
        return received
    finally:
        if connection is not None:
            connection.close()


def get_default_chat_id(bot: Any) -> str:
    """Return the latest chat ID exposed by Telegram getUpdates."""
    async def _updates() -> Any:
        return await bot.get_updates()

    updates = asyncio.run(_updates())
    for update in reversed(updates or []):
        chat = getattr(getattr(update, "effective_chat", None), "id", None)
        if chat is not None:
            return str(chat)
    raise LookupError("Telegram getUpdates returned no chat id")


def send_message(
    bot: Any,
    chat_id: str | int,
    text: str,
) -> Any:
    """Send one Telegram message through python-telegram-bot 22.x."""
    if not str(chat_id).strip():
        raise ValueError("Telegram chat_id cannot be empty")
    if not text.strip():
        raise ValueError("Telegram message cannot be empty")

    async def _send() -> Any:
        return await bot.send_message(chat_id=chat_id, text=text)

    return asyncio.run(_send())


def send_document(
    bot: Any,
    chat_id: str | int,
    file_path: str | Path,
    *,
    max_bytes: int = 50 * 1024 * 1024,
) -> Any:
    """Send a validated local document through python-telegram-bot."""
    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Telegram document is not a regular file: {path}")
    if path.stat().st_size > max_bytes:
        raise ValueError(f"Telegram document exceeds {max_bytes} bytes")

    async def _send() -> Any:
        with path.open("rb") as document:
            return await bot.send_document(chat_id=chat_id, document=document)

    return asyncio.run(_send())


def create_bot(token: str) -> Any:
    """Create a python-telegram-bot Bot without persisting the token."""
    from telegram import Bot

    return Bot(token=token)


def ask_for_bot_token(
    bot: Any,
    *,
    prompt: str = "Telegram bot token required (input hidden; never echoed): ",
    token_reader: Callable[[str], str] | None = None,
    db_path: str | Path = DEFAULT_DB,
) -> str:
    """Read a token without echoing it and assign it to the supplied bot.

    ``token_reader`` is injectable for tests. The bot only needs a writable
    ``token`` attribute, so the same function works with a real PTB bot
    configuration object or the local mock.
    """
    db_path = Path(db_path)
    require_extension_ready(db_path, ARTIFACT_NAME)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        reader = token_reader or getpass
        token = reader(prompt).strip()
    if not token:
        raise ValueError("Telegram bot token cannot be empty")
    bot.token = token
    set_configuration_state(db_path, ARTIFACT_NAME)
    return token
