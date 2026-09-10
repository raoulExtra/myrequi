"""Adapter for communication with the pi-session bridge."""

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional


class PiBridgeClient:
    """Locate and communicate with one pi-session bridge process."""

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)

    def binary(self) -> Optional[Path]:
        """Return the first available bridge executable."""
        candidates = [
            self.workspace / ".pi/bin/pi-bridge",
            Path.home() / ".pi/agent/bin/pi-bridge",
            Path.home() / ".pi/agent/npm/node_modules/@vanillagreen/pi-session-bridge/bin/pi-bridge.js",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def command(self, *args: str, timeout: int = 20) -> Any:
        """Run a bridge command and decode its JSON response."""
        bridge = self.binary()
        if bridge is None:
            raise FileNotFoundError("pi-bridge CLI not found")
        command = ["node", str(bridge), *args] if bridge.suffix == ".js" else [str(bridge), *args]
        output = subprocess.check_output(
            command, text=True, stderr=subprocess.STDOUT, timeout=timeout
        )
        return json.loads(output)

    def select_pid(self) -> Optional[int]:
        """Select an alive bridge in the current workspace when possible."""
        try:
            instances = self.command("list", "--json")
        except Exception:
            return None
        if not isinstance(instances, list):
            return None
        matches = [
            instance for instance in instances
            if instance.get("cwd") == str(self.workspace)
            and instance.get("alive")
            and instance.get("socketExists")
        ]
        if not matches:
            matches = [
                instance for instance in instances
                if instance.get("alive") and instance.get("socketExists")
            ]
        return int(matches[0]["pid"]) if matches else None

    def request(self, pid: int, payload: Dict[str, Any], timeout: int = 20) -> Any:
        """Send a JSON request to a bridge process."""
        request = dict(payload)
        request.setdefault("id", f"iar-{int(time.time() * 1000)}")
        return self.command("request", "--pid", str(pid), json.dumps(request), timeout=timeout)

    @staticmethod
    def extract_tool_text(history_response: Dict[str, Any], tool_name: str) -> Optional[str]:
        """Extract the latest text result for a named tool from bridge history."""
        events = ((history_response or {}).get("data") or {}).get("events") or []
        for event in reversed(events):
            data = event.get("data") or {}
            if event.get("event") != "tool_execution_end" or data.get("toolName") != tool_name:
                continue
            result = data.get("result") or {}
            for chunk in result.get("content") or []:
                if isinstance(chunk, dict) and chunk.get("type") == "text" and chunk.get("text"):
                    return chunk["text"]
        return None
