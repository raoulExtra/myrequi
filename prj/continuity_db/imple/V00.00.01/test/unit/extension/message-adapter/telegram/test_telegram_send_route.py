import importlib.util
from pathlib import Path
import tempfile


ADAPTER = Path(__file__).resolve().parents[5] / "extension/messenger-adapter/telegram/telegram_adapter.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("telegram_adapter_test", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeBot:
    async def get_updates(self, **kwargs):
        update = type("Update", (), {
            "update_id": 7,
            "effective_chat": type("Chat", (), {"id": 987, "type": "private"})(),
            "effective_user": type("User", (), {"id": 654, "is_bot": False})(),
            "effective_message": type("Message", (), {"text": "incoming"})(),
        })()
        return [update]

    async def send_message(self, *, chat_id, text):
        return type("Message", (), {"message_id": 42, "chat_id": chat_id, "text": text})()

    async def send_document(self, *, chat_id, document):
        return type("Message", (), {"message_id": 43, "chat_id": chat_id, "name": document.name})()


def test_receive_one_uses_async_get_updates():
    adapter = load_adapter()
    assert adapter.receive_one(FakeBot()) == {"update_id": 7, "chat_id": "987", "user_id": "654", "user_is_bot": False, "chat_type": "private", "text": "incoming"}


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


def test_telegram_formatting_preserves_plan_listing_text():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "core"))
    from route.input_action_execution import _telegram_format_text

    text = "Plans: prj/base/plans/001-plan-telegram-special-character-testing.md\n- p ls"
    assert _telegram_format_text(text) == text


def test_telegram_formatting_escapes_special_characters_and_renders_bold():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "core"))
    from route.input_action_execution import _telegram_format_text

    assert _telegram_format_text("**bold** <tag> & 'quote'") == "<b>bold</b> &lt;tag&gt; &amp; 'quote'"


def test_telegram_formatted_chunks_count_escaped_special_characters():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "core"))
    from route.input_action_execution import _telegram_formatted_chunks

    chunks = _telegram_formatted_chunks("&" * 4096)
    assert "".join(chunks) == "&amp;" * 4096
    assert all(len(chunk.encode("utf-16-le")) // 2 <= 4096 for chunk in chunks)
    assert len(chunks) > 1


def test_telegram_chunks_respect_utf16_limit_and_preserve_text():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "core"))
    from route.input_action_execution import _telegram_chunks

    text = "a" * 4094 + "🚀" + "日本語"
    chunks = _telegram_chunks(text)
    assert "".join(chunks) == text
    assert all(len(chunk.encode("utf-16-le")) // 2 <= 4096 for chunk in chunks)
    assert len(chunks) == 2


def test_send_message_preserves_special_characters_and_unicode():
    adapter = load_adapter()
    text = "<tag> & 'quote' \"double\" _brackets_ [x] \\slash 日本語 🚀"
    result = adapter.send_message(FakeBot(), "123", text)
    assert result.text == text


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
