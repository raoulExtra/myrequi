"""Execution services for agent-tool routing decisions."""

import importlib.util
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict


def execute_agent_tool(
    decision: Dict[str, Any],
    db_path: Path,
    bridge_client: Any,
) -> Any:
    """Execute an agent-tool decision without depending on the router class."""
    handler = decision.get("handler")
    if handler == "prj/continuity_db/imple/V00.00.01/extension/extension_state.py":
        params = decision.get("parameters") or {}
        artifact_name = params.get("group1") or params.get("artifact_name")
        import sys
        extension_root = Path(__file__).resolve().parents[2] / "extension"
        if str(extension_root) not in sys.path:
            sys.path.insert(0, str(extension_root))
        from extension_state import disable_extension, enable_extension, resolve_object_alias
        route_name = decision.get("route_name")
        if route_name == "disable_extension":
            tags = disable_extension(db_path, artifact_name)
        elif route_name == "enable_extension":
            tags = enable_extension(db_path, artifact_name)
        else:
            return {"status": "rejected", "error": f"Unsupported extension state route: {route_name}"}
        return {
            "status": "extension_state_updated",
            "route": route_name,
            "requested_name": artifact_name,
            "artifact_name": resolve_object_alias(artifact_name),
            "tags": sorted(tags),
        }
    if handler == "context_info":
        return execute_context_info_tool(decision, bridge_client)
    if handler == "telegram_receive_one":
        adapter_path = Path(__file__).resolve().parents[2] / "extension/messenger-adapter/telegram/telegram_adapter.py"
        spec = importlib.util.spec_from_file_location("telegram_adapter", adapter_path)
        if spec is None or spec.loader is None:
            return {"status": "unavailable", "handler": handler, "error": "Telegram adapter could not be loaded"}
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        bridge = getattr(bridge_client, "_bridge_client", bridge_client)
        bot = getattr(bridge, "telegram_bot", None)
        if bot is None:
            token = adapter.ask_for_bot_token(type("EphemeralBot", (), {})(), db_path=db_path)
            bot = adapter.create_bot(token)
        received = adapter.receive_one(bot, db_path=db_path)
        return {"status": "telegram_message_received", "handler": handler, "message": received, "token_persisted": False}
    if handler == "telegram_send_document":
        adapter_path = Path(__file__).resolve().parents[2] / "extension/messenger-adapter/telegram/telegram_adapter.py"
        spec = importlib.util.spec_from_file_location("telegram_adapter", adapter_path)
        if spec is None or spec.loader is None:
            return {"status": "unavailable", "handler": handler, "error": "Telegram adapter could not be loaded"}
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        params = decision.get("parameters") or {}
        file_path = params.get("group1") or params.get("file_path")
        bridge = getattr(bridge_client, "_bridge_client", bridge_client)
        bot = getattr(bridge, "telegram_bot", None)
        if bot is None:
            token = adapter.ask_for_bot_token(type("EphemeralBot", (), {})(), db_path=db_path)
            bot = adapter.create_bot(token)
        chat_id = adapter.get_default_chat_id(bot)
        result = adapter.send_document(bot, chat_id, str(file_path or ""))
        return {
            "status": "telegram_document_sent",
            "handler": handler,
            "chat_id": str(chat_id),
            "file_path": str(file_path),
            "message_id": getattr(result, "message_id", None),
            "token_persisted": False,
        }
    if handler == "telegram_send_message":
        adapter_path = Path(__file__).resolve().parents[2] / "extension/messenger-adapter/telegram/telegram_adapter.py"
        spec = importlib.util.spec_from_file_location("telegram_adapter", adapter_path)
        if spec is None or spec.loader is None:
            return {"status": "unavailable", "handler": handler, "error": "Telegram adapter could not be loaded"}
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        params = decision.get("parameters") or {}
        chat_id = params.get("chat_id")
        message = params.get("message")
        if not message:
            if params.get("group2"):
                chat_id = params.get("group1")
                message = params.get("group2")
            else:
                message = params.get("group1")
        bridge = getattr(bridge_client, "_bridge_client", bridge_client)
        bot = getattr(bridge, "telegram_bot", None)
        if bot is None:
            token = adapter.ask_for_bot_token(type("EphemeralBot", (), {})(), db_path=db_path)
            bot = adapter.create_bot(token)
        if not chat_id:
            chat_id = adapter.get_default_chat_id(bot)
        result = adapter.send_message(bot, chat_id, str(message or ""))
        return {
            "status": "telegram_message_sent",
            "handler": handler,
            "chat_id": str(chat_id),
            "message_id": getattr(result, "message_id", None),
            "token_persisted": False,
        }
    if handler == "prj/continuity_db/imple/V00.00.01/extension/messenger-adapter/telegram/telegram_adapter.py":
        adapter_path = Path(__file__).resolve().parents[2] / "extension/messenger-adapter/telegram/telegram_adapter.py"
        spec = importlib.util.spec_from_file_location("telegram_adapter", adapter_path)
        if spec is None or spec.loader is None:
            return {"status": "unavailable", "handler": handler, "error": "Telegram adapter could not be loaded"}
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)

        class EphemeralBot:
            token = None

        bridge = getattr(bridge_client, "_bridge_client", bridge_client)
        bot = getattr(bridge, "telegram_bot", None) or EphemeralBot()
        token_reader = getattr(bridge, "telegram_token_reader", None)
        token = adapter.ask_for_bot_token(bot, token_reader=token_reader, db_path=db_path)
        return {
            "status": "executed_agent",
            "handler": handler,
            "configured": bool(token),
            "token_persisted": False,
            "user_signal": "Telegram bot token was required and accepted through hidden input.",
        }
    if handler == "controlled_tag_assign":
        groups = (decision.get("parameters") or {}).get("groups") or []
        if len(groups) != 3:
            return {"status": "rejected", "reason": "controlled tag route requires object type, object key, and existing tag"}
        from continuity_db_helper import _controlled_tag_assign
        try:
            with sqlite3.connect(db_path) as con:
                con.row_factory = sqlite3.Row
                result = _controlled_tag_assign(con, groups[0], groups[1], groups[2])
        except ValueError as error:
            return {
                "status": "rejected",
                "code": getattr(error, "code", "tagging_not_possible"),
                "message": str(error),
                "details": getattr(error, "details", {}),
            }
        return result
    return {"status": "executed_agent", "handler": handler}


def execute_context_info_tool(decision: Dict[str, Any], bridge_client: Any) -> Any:
    """Request context information through the bridge and observe its result."""
    select_pid = getattr(bridge_client, "select_pid", None) or bridge_client._select_bridge_pid
    request = getattr(bridge_client, "request", None) or bridge_client._bridge_request
    extract_tool_text = getattr(bridge_client, "extract_tool_text", None) or bridge_client._extract_tool_text
    pid = select_pid()
    if pid is None:
        return {
            "status": "executed_agent",
            "handler": "context_info",
            "available": False,
            "error": "No active pi-session-bridge target found",
        }

    try:
        commands_response = request(pid, {"type": "get_commands"})
        commands = (((commands_response or {}).get("data") or {}).get("commands") or [])
        command_names = {cmd.get("name") for cmd in commands if isinstance(cmd, dict)}
        has_context_info = "context_info" in command_names
        send_response = request(pid, {"type": "send", "message": "/context_info"})

        result_text = None
        for _ in range(5):
            history_response = request(
                pid, {"type": "history", "limit": 20, "event": "tool_execution_end"}
            )
            result_text = extract_tool_text(history_response, "context_info")
            if result_text:
                break
            time.sleep(0.25)

        if result_text:
            return {
                "status": "executed_agent",
                "handler": "context_info",
                "available": has_context_info,
                "pid": pid,
                "bridge": send_response,
                "result": result_text,
            }

        bridge_data = (send_response or {}).get("data") if isinstance(send_response, dict) else {}
        slash_error = bridge_data.get("slashDispatchError") if isinstance(bridge_data, dict) else None
        slash_fallback = bridge_data.get("slashDispatchFallback") if isinstance(bridge_data, dict) else None
        detail = "context_info tool result was not observed in bridge history"
        if slash_error or slash_fallback:
            detail += f"; slashDispatchFallback={slash_fallback}; slashDispatchError={slash_error}"
        return {
            "status": "unavailable",
            "handler": "context_info",
            "available": False,
            "pid": pid,
            "bridge": send_response,
            "warning": detail,
            "result": detail,
        }
    except Exception as exc:
        return {
            "status": "executed_agent",
            "handler": "context_info",
            "available": False,
            "pid": pid,
            "error": str(exc),
        }
