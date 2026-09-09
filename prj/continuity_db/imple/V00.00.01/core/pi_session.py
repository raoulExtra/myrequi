#!/usr/bin/env python3
"""Helpers for prompting the live Pi session bridge."""

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

BRIDGE = Path.home() / ".pi/agent/npm/node_modules/@vanillagreen/pi-session-bridge/bin/pi-bridge.js"
__version__ = '0.0.0-placeholder'


def get_version():
    return __version__


def run_bridge(args):
    return subprocess.check_output(["node", str(BRIDGE), *args], text=True)


def get_session_state(pid: Optional[str] = None) -> Dict[str, Any]:
    target = ["--pid", str(pid)] if pid else []
    return json.loads(run_bridge(["state", *target]).strip())


def send_prompt(prompt: str, pid: Optional[str] = None) -> Dict[str, Any]:
    target = ["--pid", str(pid)] if pid else []
    return json.loads(run_bridge(["send", *target, prompt]).strip())


def set_model(provider: str, model_id: str, pid: Optional[str] = None) -> Dict[str, Any]:
    target = ["--pid", str(pid)] if pid else []
    return json.loads(run_bridge(["set-model", *target, provider, model_id]).strip())


def get_session_history(pid: Optional[str] = None, limit: int = 20, since: Optional[str] = None, event: str = "message_update", max_bytes: Optional[int] = None) -> Dict[str, Any]:
    target = ["--pid", str(pid)] if pid else []
    args = ["history", *target, str(limit), "--verbose", "--event", event]
    if since:
        args.extend(["--since", since])
    if max_bytes is not None:
        args.extend(["--max-bytes", str(max_bytes)])
    return json.loads(run_bridge(args).strip())


def _join_text_parts(parts: list[str]) -> Optional[str]:
    """Join extracted bridge text chunks, suppressing adjacent duplicates.

    Some pi-session-bridge message_update snapshots can contain the same final
    text more than once (for example two adjacent ``"err"`` chunks).  Treat that
    as a transport/history duplication artifact while preserving non-adjacent or
    different chunks.
    """
    deduped: list[str] = []
    for part in parts:
        text = part.strip()
        if not text:
            continue
        if deduped and deduped[-1] == text:
            continue
        deduped.append(text)
    if deduped:
        return "\n".join(deduped).strip()
    return None


def _extract_text_from_node(node: Any) -> Optional[str]:
    if isinstance(node, str):
        text = node.strip()
        return text or None
    if isinstance(node, list):
        parts = []
        for item in node:
            found = _extract_text_from_node(item)
            if found:
                parts.append(found)
        return _join_text_parts(parts)
    if not isinstance(node, dict):
        return None

    node_type = node.get("type")
    if node_type in {"thinking", "toolCall"}:
        # These are useful for debugging but are not the answer text.
        if node_type == "toolCall":
            return None

    parts = []
    for key in ("text", "result", "output", "message", "content", "partial", "response"):
        if key not in node:
            continue
        found = _extract_text_from_node(node.get(key))
        if found:
            parts.append(found)
    return _join_text_parts(parts)


def _iter_assistant_text_candidates(history: Dict[str, Any], since: Optional[str] = None):
    events = ((history or {}).get("data") or {}).get("events") or []
    for event in reversed(events):
        if since:
            event_ts = event.get("timestamp") or ((event.get("data") or {}).get("message") or {}).get("timestamp")
            if isinstance(event_ts, str) and event_ts <= since:
                continue
        data = event.get("data") or {}
        for key in ("assistantMessageEvent", "message", "partial", "response"):
            candidate = data.get(key)
            if candidate is not None:
                yield candidate
        yield data


def _extract_assistant_text(history: Dict[str, Any], since: Optional[str] = None) -> Optional[str]:
    for candidate in _iter_assistant_text_candidates(history, since=since):
        if isinstance(candidate, dict):
            role = candidate.get("role")
            stop_reason = candidate.get("stopReason")
            if role and role != "assistant":
                continue
            if stop_reason == "pending":
                found = _extract_text_from_node(candidate.get("content"))
                if found:
                    return found
                continue
        found = _extract_text_from_node(candidate)
        if found:
            return found
    return None


def latest_assistant_text(pid: Optional[str] = None, limit: int = 50, since: Optional[str] = None) -> Optional[str]:
    history = get_session_history(pid=pid, limit=limit, since=since)
    return _extract_assistant_text(history or {}, since=since)


def _stream_session_observation(event: Dict[str, Any], state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    event_type = event.get("type")
    obs: Dict[str, Any] = {"type": event_type}

    def attach_state() -> None:
        obs["state"] = {
            "assistant_text": state["assistant_text"],
            "last_error": state["last_error"],
            "last_retry": state["last_retry"],
            "queue": state["queue"],
        }

    if event_type == "session":
        obs["kind"] = "session_header"
        obs["sessionId"] = event.get("id")
        obs["cwd"] = event.get("cwd")
        return obs

    if event_type == "message_update":
        ae = event.get("assistantMessageEvent") or {}
        ae_type = ae.get("type")
        if ae_type == "text_start":
            state["assistant_text"] = ""
            obs.update(kind="assistant_text_start", contentIndex=ae.get("contentIndex"))
        elif ae_type == "text_delta":
            delta = ae.get("delta", "")
            state["assistant_text"] += delta
            obs.update(kind="assistant_text_delta", contentIndex=ae.get("contentIndex"), delta=delta)
        elif ae_type == "text_end":
            end_text = ae.get("content")
            if not isinstance(end_text, str) or not end_text.strip():
                end_text = state["assistant_text"]
            else:
                state["assistant_text"] = end_text
            obs.update(kind="assistant_text_end", contentIndex=ae.get("contentIndex"), text=end_text)
        elif ae_type == "toolcall_start":
            obs.update(kind="tool_call_start", contentIndex=ae.get("contentIndex"), tool=ae.get("toolName"), id=ae.get("id"))
        elif ae_type == "toolcall_delta":
            obs.update(kind="tool_call_delta", contentIndex=ae.get("contentIndex"), delta=ae.get("delta", ""), id=ae.get("id"))
        elif ae_type == "toolcall_end":
            tool_call = ae.get("toolCall") or {}
            obs.update(kind="tool_call_end", contentIndex=ae.get("contentIndex"), tool=tool_call.get("name") or ae.get("toolName"), toolCall=tool_call, id=tool_call.get("id") or ae.get("id"))
        elif ae_type == "thinking_start":
            obs.update(kind="assistant_thinking_start", contentIndex=ae.get("contentIndex"))
        elif ae_type == "thinking_delta":
            obs.update(kind="assistant_thinking_delta", contentIndex=ae.get("contentIndex"), delta=ae.get("delta", ""))
        elif ae_type == "thinking_end":
            obs.update(kind="assistant_thinking_end", contentIndex=ae.get("contentIndex"), thinking=ae.get("thinking"))
        else:
            obs.update(kind="assistant_message_update", assistantMessageEvent=ae)
        attach_state()
        return obs

    if event_type == "message_end":
        msg = event.get("message") or {}
        if msg.get("role") == "assistant":
            text = _extract_text_from_node(msg.get("content"))
            if text:
                state["assistant_text"] = text
            obs.update(kind="assistant_message_end", text=state["assistant_text"], stopReason=msg.get("stopReason"), message=msg)
            attach_state()
            return obs
        return None

    if event_type == "tool_execution_start":
        obs.update(kind="tool_execution_start", toolCallId=event.get("toolCallId"), tool=event.get("toolName"), args=event.get("args"))
        attach_state()
        return obs

    if event_type == "tool_execution_update":
        obs.update(kind="tool_execution_update", toolCallId=event.get("toolCallId"), tool=event.get("toolName"), partialResult=event.get("partialResult"))
        attach_state()
        return obs

    if event_type == "tool_execution_end":
        result = event.get("result")
        is_error = bool(event.get("isError"))
        obs.update(kind="tool_execution_end", toolCallId=event.get("toolCallId"), tool=event.get("toolName"), result=result, isError=is_error)
        if is_error:
            state["last_error"] = event
            obs["decision_hint"] = "tool_failed"
        attach_state()
        return obs

    if event_type == "auto_retry_start":
        state["last_retry"] = event
        obs.update(kind="retry_start", attempt=event.get("attempt"), maxAttempts=event.get("maxAttempts"), delayMs=event.get("delayMs"), errorMessage=event.get("errorMessage"), decision_hint="retrying")
        attach_state()
        return obs

    if event_type == "auto_retry_end":
        success = bool(event.get("success"))
        obs.update(kind="retry_end", success=success, attempt=event.get("attempt"), finalError=event.get("finalError"))
        if not success:
            state["last_error"] = event
            obs["decision_hint"] = "model_error"
        attach_state()
        return obs

    if event_type == "queue_update":
        state["queue"] = {
            "steering": event.get("steering", []),
            "followUp": event.get("followUp", []),
        }
        obs.update(kind="queue_update", queue=state["queue"], decision_hint="follow_up_pending" if state["queue"]["followUp"] else None)
        attach_state()
        return obs

    if event_type == "extension_error":
        state["last_error"] = event
        obs.update(kind="extension_error", error=event.get("error"), extensionPath=event.get("extensionPath"), decision_hint="extension_error")
        attach_state()
        return obs

    if event_type == "agent_end":
        obs.update(kind="agent_end", willRetry=event.get("willRetry"), messages=event.get("messages"))
        attach_state()
        return obs

    if event_type == "agent_settled":
        obs.update(kind="agent_settled")
        attach_state()
        return obs

    return None


def stream_session_observations(pid: Optional[str] = None):
    target = ["--pid", str(pid)] if pid else []
    proc = subprocess.Popen(["node", str(BRIDGE), "stream", *target], stdout=subprocess.PIPE, text=True)
    state = {
        "assistant_text": "",
        "last_error": None,
        "last_retry": None,
        "queue": {"steering": [], "followUp": []},
    }
    if proc.stdout is None:
        return

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        obs = _stream_session_observation(event, state)
        if obs is not None:
            yield obs


def prompt_session(prompt: str, pid: Optional[str] = None) -> Dict[str, Any]:
    state = get_session_state(pid=pid)
    session_pid = pid or str(((state.get("data") or {}).get("pid")) or "") or None
    started_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    response = send_prompt(prompt, pid=session_pid)

    assistant_text = None
    history = None
    broad_history = None
    for _ in range(20):
        try:
            history = get_session_history(pid=session_pid, limit=20, since=started_at)
        except Exception:
            history = None
        assistant_text = _extract_assistant_text(history or {}, since=started_at)
        if assistant_text:
            break
        time.sleep(0.5)

    if not assistant_text:
        try:
            broad_history = get_session_history(pid=session_pid, limit=50, event="message_update")
            assistant_text = _extract_assistant_text(broad_history or {}, since=None)
        except Exception:
            broad_history = None

    return {
        "prompt": prompt,
        "pid": session_pid,
        "state": state,
        "send": response,
        "history": history or broad_history,
        "assistant_text": assistant_text,
        "started_at": started_at,
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: pi_session.py <prompt> [--pid PID]", file=sys.stderr)
        raise SystemExit(2)

    pid = None
    if "--pid" in argv:
        i = argv.index("--pid")
        pid = argv[i + 1]
        del argv[i : i + 2]

    prompt = " ".join(argv).strip()
    if not prompt:
        prompt = sys.stdin.read().strip()
    if not prompt:
        print("prompt is required", file=sys.stderr)
        raise SystemExit(2)

    print(json.dumps(prompt_session(prompt, pid=pid), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
