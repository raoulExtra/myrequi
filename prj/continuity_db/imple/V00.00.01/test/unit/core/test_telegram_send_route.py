import asyncio
import importlib.util
from pathlib import Path


ADAPTER = Path(__file__).resolve().parents[5] / "imple/V00.00.01/extension/messenger-adapter/telegram/telegram_adapter.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("telegram_adapter_test", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeBot:
    async def get_updates(self):
        return [type("Update", (), {"effective_chat": type("Chat", (), {"id": 987})()})()]

    async def send_message(self, *, chat_id, text):
        return type("Message", (), {"message_id": 42, "chat_id": chat_id, "text": text})()


def test_send_message_uses_python_telegram_bot_shape():
    adapter = load_adapter()
    bot = FakeBot()
    assert adapter.get_default_chat_id(bot) == "987"
    result = adapter.send_message(bot, "123", "hello")
    assert result.message_id == 42
    assert result.chat_id == "123"
    assert result.text == "hello"


def test_default_route_pattern_extracts_message_without_chat_id():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "core"))
    from route.input_action_matching import match_routing_rule

    matched, params = match_routing_rule(
        {"pattern_type": "json_regex", "pattern_spec": r"^telegram\s+send\s+(?!-?\d+\s)(.+)$"},
        "telegram send hello from latest chat",
        None,
    )
    assert matched
    assert params["group1"] == "hello from latest chat"


def test_route_pattern_extracts_chat_id_and_message():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "core"))
    from route.input_action_matching import match_routing_rule

    matched, params = match_routing_rule(
        {"pattern_type": "json_regex", "pattern_spec": r"^telegram\s+send\s+(-?\d+)\s+(.+)$"},
        "telegram send 123 hello from route",
        None,
    )
    assert matched
    assert params["group1"] == "123"
    assert params["group2"] == "hello from route"
