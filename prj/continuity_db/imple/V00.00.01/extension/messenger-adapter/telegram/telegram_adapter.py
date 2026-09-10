"""Telegram messenger extension boundary.

The token prompt belongs to the extension, while tests can pass a mock bot
object. This module does not persist the token or contact Telegram.
"""

from __future__ import annotations

from getpass import getpass
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


def ask_for_bot_token(
    bot: Any,
    *,
    prompt: str = "Telegram bot token: ",
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
    reader = token_reader or getpass
    token = reader(prompt).strip()
    if not token:
        raise ValueError("Telegram bot token cannot be empty")
    bot.token = token
    set_configuration_state(db_path, ARTIFACT_NAME)
    return token
