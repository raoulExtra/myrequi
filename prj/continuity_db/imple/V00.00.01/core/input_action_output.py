"""Formatting helpers for displaying routed action results."""

import json
from typing import Any, Dict, List, Optional


def extract_session_text(session_result: Any) -> Optional[str]:
    """Find the first useful assistant/session text in a bridge response."""
    if not isinstance(session_result, dict):
        return None

    def pick_text(node: Any) -> Optional[str]:
        if isinstance(node, str):
            return node.strip() or None
        if isinstance(node, list):
            for item in node:
                found = pick_text(item)
                if found:
                    return found
            return None
        if isinstance(node, dict):
            for key in ("text", "message", "result", "content", "output"):
                if key in node:
                    found = pick_text(node[key])
                    if found:
                        return found
            data = node.get("data")
            if isinstance(data, dict):
                for key in ("text", "message", "result", "content", "output", "deliveredAs"):
                    value = data.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
                    found = pick_text(value)
                    if found:
                        return found
        return None

    for key in ("assistant_text", "reply_text"):
        value = session_result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    history = session_result.get("history")
    if isinstance(history, dict):
        events = ((history.get("data") or {}).get("events") or [])
        for event in reversed(events):
            data = event.get("data") or {}
            message = data.get("message") or data.get("partial")
            if not isinstance(message, dict) or message.get("role") != "assistant":
                continue
            content = message.get("content") or []
            if isinstance(content, str) and content.strip():
                return content.strip()
            if isinstance(content, list):
                for chunk in reversed(content):
                    if isinstance(chunk, dict):
                        text = chunk.get("text")
                        if isinstance(text, str) and text.strip():
                            return text.strip()

    for key in ("send", "state"):
        found = pick_text(session_result.get(key))
        if found:
            return found
    return pick_text(session_result)


def format_plain_result(result: Dict[str, Any]) -> List[str]:
    """Convert a router result into concise display lines."""
    action_result = result.get("action_result") or {}
    lines: List[str] = []
    assistant_text = action_result.get("assistant_text") or action_result.get("reply_text")
    if isinstance(assistant_text, str) and assistant_text.strip():
        return [assistant_text.strip()]
    session_text = extract_session_text(action_result.get("session_result"))
    if session_text:
        return [session_text]
    text = action_result.get("result")
    if isinstance(text, str) and text.strip():
        return [text.strip()]
    value = action_result.get("value")
    if isinstance(value, (str, int, float, bool)) and value:
        return [f"value: {value}"]
    if action_result.get("command"):
        lines.append(str(action_result["command"]))
    for key in ("message", "warning", "error"):
        value = action_result.get(key)
        if isinstance(value, str) and value.strip():
            lines.append(value.strip())
    return lines or [json.dumps(action_result, indent=2)]
