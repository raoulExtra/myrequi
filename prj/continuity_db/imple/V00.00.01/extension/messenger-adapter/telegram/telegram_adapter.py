"""Telegram messenger extension boundary.

The token prompt belongs to the extension, while tests can pass a mock bot
object. This module does not persist the token or contact Telegram.
"""

from __future__ import annotations

import asyncio
from getpass import getpass
import os
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


async def receive_one_async(bot: Any) -> dict[str, Any]:
    """Receive one pending Telegram update without persisting it."""
    updates = await bot.get_updates(limit=1)
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


def receive_one(bot: Any) -> dict[str, Any]:
    """Synchronously expose one asynchronous Telegram update."""
    return asyncio.run(receive_one_async(bot))


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
