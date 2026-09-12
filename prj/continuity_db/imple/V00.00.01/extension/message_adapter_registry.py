"""Registry and delivery boundary for active message adapters."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any

from extension_state import extension_tags, require_extension_ready


ADAPTERS = {
    "messenger-adapter.telegramm": Path(__file__).parent / "messenger-adapter/telegram/telegram_adapter.py",
}


def active_message_adapters(db_path: str | Path) -> list[tuple[str, Path]]:
    """Return installed and enabled adapters in deterministic order."""
    active = []
    for artifact_name, module_path in sorted(ADAPTERS.items()):
        try:
            require_extension_ready(db_path, artifact_name)
            tags = extension_tags(db_path, artifact_name)
        except Exception:
            continue
        if not {"kind:messenger-adapter", "activation:enabled"}.issubset(tags):
            continue
        if module_path.is_file():
            active.append((artifact_name, module_path))
    return active


def load_adapter(module_path: Path) -> Any:
    name = f"message_adapter_{module_path.stem}"
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Message adapter could not be loaded: {module_path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def send_document_to_active_adapters(
    db_path: str | Path,
    bridge_client: Any,
    file_path: str | Path,
) -> list[dict[str, Any]]:
    """Send one local document through every active messenger adapter."""
    sent = []
    for artifact_name, module_path in active_message_adapters(db_path):
        adapter = load_adapter(module_path)
        bridge = getattr(bridge_client, "_bridge_client", bridge_client)
        bot = getattr(bridge, "telegram_bot", None)
        if bot is None:
            token = adapter.ask_for_bot_token(type("EphemeralBot", (), {})(), db_path=db_path)
            bot = adapter.create_bot(token)
        chat_id = os.environ.get("TELEGRAM_ALLOWED_CHAT_ID") or adapter.get_default_chat_id(bot)
        result = adapter.send_document(bot, chat_id, file_path)
        sent.append({
            "adapter": artifact_name,
            "message_id": getattr(result, "message_id", None),
        })
    return sent


def send_to_active_adapters(
    db_path: str | Path,
    bridge_client: Any,
    text: str,
) -> list[dict[str, Any]]:
    """Send text through every active adapter using the common adapter contract."""
    if not str(text).strip():
        return []
    sent = []
    for artifact_name, module_path in active_message_adapters(db_path):
        adapter = load_adapter(module_path)
        bridge = getattr(bridge_client, "_bridge_client", bridge_client)
        bot = getattr(bridge, "telegram_bot", None)
        if bot is None:
            token = adapter.ask_for_bot_token(type("EphemeralBot", (), {})(), db_path=db_path)
            bot = adapter.create_bot(token)
        chat_id = os.environ.get("TELEGRAM_ALLOWED_CHAT_ID") or adapter.get_default_chat_id(bot)
        result = adapter.send_message(bot, chat_id, text)
        sent.append({
            "adapter": artifact_name,
            "message_id": getattr(result, "message_id", None),
        })
    return sent
