"""Execution services for agent-tool routing decisions."""

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
    if handler == "context_info":
        return execute_context_info_tool(decision, bridge_client)
    if handler == "controlled_tag_assign":
        groups = (decision.get("parameters") or {}).get("groups") or []
        if len(groups) != 3:
            return {"status": "rejected", "reason": "controlled tag route requires object type, object key, and existing tag"}
        from helper_for_db import _controlled_tag_assign
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
