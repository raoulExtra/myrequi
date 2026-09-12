"""Execution services for agent-tool routing decisions."""

import asyncio
import html
import importlib.util
import json
import os
import re
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict


TELEGRAM_POLL_PID_PATH = Path('/tmp/myrequi-telegram-poll.pid')
TELEGRAM_POLL_USER_PATH = Path('/tmp/myrequi-telegram-poll-user.id')
TELEGRAM_REJECTED_DIR = Path('/tmp/myrequi-telegram-rejected')


def _record_rejected_telegram_message(message: Dict[str, Any], reason: str) -> str:
    """Write a restricted audit record for an unauthorized Telegram message."""
    TELEGRAM_REJECTED_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    timestamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    update_id = str(message.get('update_id') or 'unknown')
    path = TELEGRAM_REJECTED_DIR / f'{timestamp}-{update_id}.json'
    payload = {
        'timestamp': timestamp,
        'reason': reason,
        'user_id': message.get('user_id'),
        'chat_id': message.get('chat_id'),
        'chat_type': message.get('chat_type'),
        'text': message.get('text'),
        'update_id': message.get('update_id'),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\\n')
    path.chmod(0o600)
    return str(path)


def _telegram_message_is_allowed(message: Dict[str, Any]) -> tuple[bool, str | None]:
    """Enforce Telegram identity restrictions before exposing a message."""
    allowed_user_id = os.environ.get("TELEGRAM_ALLOWED_USER_ID")
    allowed_chat_id = os.environ.get("TELEGRAM_ALLOWED_CHAT_ID")
    require_private = os.environ.get("TELEGRAM_REQUIRE_PRIVATE", "1") != "0"
    if not allowed_user_id:
        return False, "TELEGRAM_ALLOWED_USER_ID is not configured"
    if require_private and message.get("chat_type") != "private":
        return False, "Telegram message is not from a private chat"
    if message.get("user_is_bot") is True:
        return False, "Telegram message is from a bot"
    if str(message.get("user_id")) != str(allowed_user_id):
        return False, "Telegram message user is not allowed"
    if allowed_chat_id is not None and str(message.get("chat_id")) != str(allowed_chat_id):
        return False, "Telegram message chat is not allowed"
    return True, None


def _telegram_package_command_is_blocked(text: str) -> bool:
    """Block package-install command forms while leaving future routes available."""
    return re.search(
        r"(?:^|[;&|`\s])(?:sudo\s+)?(?:pip3?|python(?:3)?\s+-m\s+pip)(?=\s|$)",
        text.strip(),
        re.IGNORECASE,
    ) is not None


def _telegram_sandbox_notice_required(text: str) -> bool:
    """Give a fixed sandbox response for non-command pip questions."""
    return re.search(r"\bpip3?\b", text, re.IGNORECASE) is not None


def _telegram_debug_enabled(router: Any) -> bool:
    row = router.conn.execute(
        "SELECT enabled FROM feature_flags WHERE feature_key='debug_mode' LIMIT 1"
    ).fetchone()
    return bool(row and row[0])


def _telegram_format_text(text: str) -> str:
    """Convert common Markdown bold to safe Telegram HTML."""
    escaped = html.escape(str(text), quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped, flags=re.DOTALL)


def _telegram_chunks(text: str, limit: int = 4096) -> list[str]:
    """Split text without exceeding Telegram's UTF-16 code-unit limit."""
    chunks, current, units = [], [], 0
    for character in str(text):
        width = len(character.encode("utf-16-le")) // 2
        if current and units + width > limit:
            chunks.append("".join(current))
            current, units = [], 0
        current.append(character)
        units += width
    if current:
        chunks.append("".join(current))
    return chunks


def _telegram_formatted_chunks(text: str, limit: int = 4096) -> list[str]:
    """Format first so escaped HTML is included in the Telegram limit."""
    return _telegram_chunks(_telegram_format_text(text), limit=limit)


def _telegram_update_is_new(update_id: Any, last_update_id: int | None) -> tuple[bool, int | None]:
    """Accept each ordered Telegram update at most once per poller."""
    if update_id is None:
        return True, last_update_id
    try:
        current_update_id = int(update_id)
    except (TypeError, ValueError):
        return True, last_update_id
    if last_update_id is not None and current_update_id <= last_update_id:
        return False, last_update_id
    return True, current_update_id


def _telegram_action_response(result: Dict[str, Any], debug: bool) -> str:
    if debug:
        return json.dumps(result, ensure_ascii=False)
    action_result = result.get("action_result") or result.get("mode_result")
    if isinstance(action_result, dict) and isinstance(action_result.get("mode_result"), dict):
        action_result = action_result["mode_result"]
    if isinstance(action_result, dict):
        message = action_result.get("message")
        if message:
            return str(message)
        output = action_result.get("result")
        if isinstance(output, str) and output:
            return output
        status = action_result.get("status")
        if status:
            return str(status).replace("_", " ").capitalize() + "."
    return "Action completed." if result.get("success", True) else "Action failed."


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
    if handler == "play_media":
        params = decision.get("parameters") or {}
        bell_volume = params.get("group1")
        file_name = params.get("group2")
        file_volume = params.get("group3")
        media_kind = "file" if file_name else "bell"
        volume_value = file_volume if file_name else bell_volume
        try:
            volume = max(0, min(100, int(volume_value or 100)))
        except (TypeError, ValueError):
            return {"status": "rejected", "handler": handler, "error": "volume must be 0-100"}
        project_root = Path(__file__).resolve().parents[6]
        if media_kind == "bell":
            media_path = project_root / "prj/continuity_db/assets/media/ui_noti_bell.mp3"
        else:
            media_path = Path(str(file_name)).expanduser()
            if not media_path.is_absolute():
                media_path = project_root / media_path
            media_path = media_path.resolve()
        if not media_path.is_file():
            return {"status": "unavailable", "handler": handler, "error": f"media file not found: {media_path}"}
        process = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", "-volume", str(volume), str(media_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {
            "status": "media_playback_started",
            "handler": handler,
            "media": media_kind,
            "file": str(media_path),
            "volume": volume,
            "pid": process.pid,
        }
    if handler == "telegram_stop_poll":
        if not TELEGRAM_POLL_PID_PATH.exists():
            return {"status": "telegram_poll_not_running", "handler": handler}
        try:
            poll_pid = int(TELEGRAM_POLL_PID_PATH.read_text().strip())
            os.kill(poll_pid, signal.SIGTERM)
            TELEGRAM_POLL_PID_PATH.unlink(missing_ok=True)
            TELEGRAM_POLL_USER_PATH.unlink(missing_ok=True)
            return {"status": "telegram_poll_stopped", "handler": handler, "pid": poll_pid}
        except (ValueError, ProcessLookupError):
            TELEGRAM_POLL_PID_PATH.unlink(missing_ok=True)
            return {"status": "telegram_poll_not_running", "handler": handler}
    if handler == "telegram_poll":
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
        TELEGRAM_POLL_PID_PATH.write_text(str(os.getpid()))

        async def poll_forever() -> None:
            allowed_chat_id = os.environ.get("TELEGRAM_ALLOWED_CHAT_ID")
            user_file_exists = TELEGRAM_POLL_USER_PATH.exists()
            allowed_user_id = os.environ.get("TELEGRAM_ALLOWED_USER_ID")
            if allowed_user_id is None and user_file_exists:
                allowed_user_id = TELEGRAM_POLL_USER_PATH.read_text().strip() or None
            require_private = os.environ.get("TELEGRAM_REQUIRE_PRIVATE", "1") != "0"
            last_update_id = None
            while True:
                try:
                    received = await adapter.receive_one_async(bot)
                except LookupError:
                    await asyncio.sleep(2)
                    continue
                is_new_update, last_update_id = _telegram_update_is_new(
                    received.get("update_id"), last_update_id
                )
                if not is_new_update:
                    continue
                chat_id = received.get("chat_id")
                user_id = received.get("user_id")
                if require_private and received.get("chat_type") != "private":
                    continue
                if received.get("user_is_bot") is True:
                    continue
                if allowed_chat_id is None:
                    allowed_chat_id = chat_id
                if allowed_user_id is None:
                    allowed_user_id = user_id
                    if not user_file_exists:
                        TELEGRAM_POLL_USER_PATH.write_text(str(allowed_user_id))
                        TELEGRAM_POLL_USER_PATH.chmod(0o600)
                if chat_id != allowed_chat_id or user_id != allowed_user_id:
                    # Acknowledge but never forward another chat's message.
                    continue
                text = received.get("text") or ""
                if text.startswith("X "):
                    prompt = text[2:].strip()
                    if _telegram_package_command_is_blocked(prompt):
                        await bot.send_message(
                            chat_id=chat_id,
                            text="Blocked: package-install commands are unavailable from Telegram.",
                            parse_mode="HTML",
                        )
                        continue
                    if _telegram_sandbox_notice_required(prompt):
                        await bot.send_message(
                            chat_id=chat_id,
                            text="You are in a sandbox.",
                            parse_mode="HTML",
                        )
                        continue
                    router = bridge_client if hasattr(bridge_client, "match_input_to_route") else None
                    if router is not None and router._route_mode_enabled():
                        decision = router.match_input_to_route(prompt, "text")
                        if (decision.get("recall_packet") or {}).get("recursion_blocked"):
                            await bot.send_message(chat_id=chat_id, text="No recursion here.", parse_mode="HTML")
                            continue
                        if (
                            decision.get("route_type") in {"control_command", "agent_tool"}
                            and decision.get("route_name") != "session_prompt"
                            and router._no_recursion_route_hit({"route_name": decision.get("route_name")})
                        ):
                            await bot.send_message(chat_id=chat_id, text="No recursion here.", parse_mode="HTML")
                            continue
                        if decision.get("route_type") in {"control_command", "agent_tool"} and decision.get("route_name") != "session_prompt":
                            routed_result = router.execute_routing_decision(decision, prompt)
                            response_text = _telegram_action_response(
                                routed_result, _telegram_debug_enabled(router)
                            )
                            for chunk in _telegram_formatted_chunks(response_text):
                                await bot.send_message(
                                    chat_id=chat_id,
                                    text=chunk,
                                    parse_mode="HTML",
                                )
                            continue
                    project_root = Path(__file__).resolve().parents[6]
                    if str(project_root) not in sys.path:
                        sys.path.insert(0, str(project_root))
                    from pi_session import prompt_session
                    select_pid = getattr(bridge_client, "_select_bridge_pid", None)
                    pid = select_pid() if select_pid else None
                    session_result = prompt_session(prompt, pid=pid)
                    assistant_text = str(session_result.get("assistant_text") or "").strip()
                    if assistant_text:
                        # Telegram limits text messages to 4096 characters.
                        for chunk in _telegram_formatted_chunks(assistant_text):
                            await bot.send_message(
                                chat_id=chat_id,
                                text=chunk,
                                parse_mode="HTML",
                            )

        try:
            asyncio.run(poll_forever())
        finally:
            TELEGRAM_POLL_PID_PATH.unlink(missing_ok=True)
            TELEGRAM_POLL_USER_PATH.unlink(missing_ok=True)
        return {"status": "telegram_poll_stopped", "handler": handler}
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
        allowed, rejection_reason = _telegram_message_is_allowed(received)
        if not allowed:
            rejection_log_path = _record_rejected_telegram_message(received, rejection_reason or "Telegram message rejected")
            return {
                "status": "telegram_message_rejected",
                "handler": handler,
                "reason": rejection_reason,
                "rejection_log_path": rejection_log_path,
                "message": received,
                "token_persisted": False,
            }
        return {"status": "telegram_message_received", "handler": handler, "message": received, "token_persisted": False}
    if handler == "execute_bash":
        params = decision.get("parameters") or {}
        command = params.get("group1") or params.get("command") or ""
        if not str(command).strip():
            return {"status": "rejected", "handler": handler, "error": "Bash command is required"}
        try:
            completed = subprocess.run(
                ["bash", "-lc", str(command)],
                cwd=str(Path(db_path).resolve().parent),
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "status": "timeout",
                "handler": handler,
                "command": str(command),
                "stdout": (exc.stdout or "") if isinstance(exc.stdout, str) else "",
                "stderr": (exc.stderr or "") if isinstance(exc.stderr, str) else "",
            }
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        return {
            "status": "bash_completed" if completed.returncode == 0 else "bash_failed",
            "handler": handler,
            "command": str(command),
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "result": stdout.rstrip("\n") or stderr.rstrip("\n"),
        }
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
            chat_id = os.environ.get("TELEGRAM_ALLOWED_CHAT_ID") or adapter.get_default_chat_id(bot)
        result = adapter.send_message(bot, chat_id, str(message or ""))
        return {
            "status": "telegram_message_sent",
            "handler": handler,
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
