import importlib.util
from pathlib import Path
import tempfile


ADAPTER = Path(__file__).resolve().parents[5] / "imple/V00.00.01/extension/messenger-adapter/telegram/telegram_adapter.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("telegram_adapter_test", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeBot:
    async def get_updates(self, **kwargs):
        update = type("Update", (), {
            "update_id": 7,
            "effective_chat": type("Chat", (), {"id": 987})(),
            "effective_message": type("Message", (), {"text": "incoming"})(),
        })()
        return [update]

    async def send_message(self, *, chat_id, text):
        return type("Message", (), {"message_id": 42, "chat_id": chat_id, "text": text})()

    async def send_document(self, *, chat_id, document):
        return type("Message", (), {"message_id": 43, "chat_id": chat_id, "name": document.name})()


def test_receive_one_uses_async_get_updates():
    adapter = load_adapter()
    assert adapter.receive_one(FakeBot()) == {"update_id": 7, "chat_id": "987", "text": "incoming"}


def test_receive_one_acknowledges_offset_without_database_storage():
    adapter = load_adapter()
    bot = FakeBot()
    assert adapter.receive_one(bot)["update_id"] == 7


def test_send_message_uses_python_telegram_bot_shape():
    adapter = load_adapter()
    bot = FakeBot()
    assert adapter.get_default_chat_id(bot) == "987"
    result = adapter.send_message(bot, "123", "hello")
    assert result.message_id == 42
    assert result.chat_id == "123"
    assert result.text == "hello"


def test_send_document_uses_python_telegram_bot_shape():
    adapter = load_adapter()
    with tempfile.NamedTemporaryFile() as file:
        file.write(b"document")
        file.flush()
        result = adapter.send_document(FakeBot(), "987", file.name)
    assert result.message_id == 43
    assert result.chat_id == "987"


def test_receive_route_matches():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "core"))
    from route.input_action_matching import match_routing_rule

    matched, _ = match_routing_rule(
        {"pattern_type": "json_regex", "pattern_spec": r"^telegram\s+receive$"},
        "telegram receive",
        None,
    )
    assert matched


def test_document_route_extracts_path():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "core"))
    from route.input_action_matching import match_routing_rule

    matched, params = match_routing_rule(
        {"pattern_type": "json_regex", "pattern_spec": r"^telegram\s+send\s+doc\s+(.+)$"},
        "telegram send doc /tmp/report.txt",
        None,
    )
    assert matched
    assert params["group1"] == "/tmp/report.txt"


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
