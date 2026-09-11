"""Test doubles for external dependencies used by route actions."""

import sys
from contextlib import contextmanager
from types import ModuleType


class MockBridgeClient:
    """Deterministic pi-session bridge replacement that records requests."""

    def __init__(self, pid=4242, command_responses=None, tool_text="mock context info"):
        self.pid = pid
        self.command_responses = command_responses or {}
        self.tool_text = tool_text
        self.telegram_bot = type("MockTelegramBot", (), {"token": None})()
        self.telegram_token_reader = lambda prompt: "mock-telegram-token"
        self.calls = []

    def binary(self):
        self.calls.append(("binary",))
        return None

    def command(self, *args, **kwargs):
        self.calls.append(("command", args, kwargs))
        return self.command_responses.get(args[0])

    def select_pid(self):
        self.calls.append(("select_pid",))
        return self.pid

    def request(self, pid, payload, timeout=20):
        self.calls.append(("request", pid, payload, timeout))
        if payload.get("type") == "get_commands":
            return {"data": {"commands": [{"name": "context_info"}]}}
        if payload.get("type") == "history":
            return {"data": {"events": []}}
        if payload.get("type") == "send":
            return {"data": {"accepted": True}}
        return {"data": {}}

    def extract_tool_text(self, history_response, tool_name):
        self.calls.append(("extract_tool_text", history_response, tool_name))
        return self.tool_text


class MockPiSession:
    """Mock pi_session API used by control-command route actions."""

    def __init__(self):
        self.calls = []

    def get_session_state(self, pid=None):
        self.calls.append(("get_session_state", pid))
        return {"context": {"model": "mock-model", "pid": pid}}

    def set_model(self, provider, model_name, pid=None):
        self.calls.append(("set_model", provider, model_name, pid))
        return {"status": "mock_model_set", "provider": provider, "model": model_name}

    def latest_assistant_text(self, pid=None):
        self.calls.append(("latest_assistant_text", pid))
        return "mock assistant response"

    def get_session_history(self, pid=None, limit=None, event=None, max_bytes=None, since=None):
        self.calls.append(("get_session_history", pid, limit, event, max_bytes, since))
        return {"data": {"events": []}}

    def prompt_session(self, prompt, pid=None):
        self.calls.append(("prompt_session", prompt, pid))
        return {"assistant_text": "mock prompted response"}


@contextmanager
def mock_pi_session():
    """Temporarily install the mock pi_session module for route-action tests."""
    mock = MockPiSession()
    module = ModuleType("pi_session")
    module.get_session_state = mock.get_session_state
    module.set_model = mock.set_model
    module.latest_assistant_text = mock.latest_assistant_text
    module.get_session_history = mock.get_session_history
    module.prompt_session = mock.prompt_session
    previous = sys.modules.get("pi_session")
    sys.modules["pi_session"] = module
    try:
        yield mock
    finally:
        if previous is None:
            sys.modules.pop("pi_session", None)
        else:
            sys.modules["pi_session"] = previous
