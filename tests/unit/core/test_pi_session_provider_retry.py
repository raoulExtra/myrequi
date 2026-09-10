import json
from pathlib import Path

import pi_session


def test_runtime_provider_error_log_uses_plan_filename():
    target = getattr(pi_session, "_module", pi_session)

    assert target.PROVIDER_ERROR_LOG.name == "provider-error.log"


def test_send_prompt_retries_provider_error_and_issues_continue(monkeypatch, tmp_path: Path):
    calls = []
    waits = []
    responses = [
        RuntimeError("provider timeout"),
        json.dumps({"type": "response", "data": {"text": "ok"}}),
        json.dumps({"type": "response", "data": {"continued": True}}),
    ]

    def fake_bridge(args):
        calls.append(args)
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    target = getattr(pi_session, "_module", pi_session)
    monkeypatch.setattr(target, "run_bridge", fake_bridge)
    monkeypatch.setattr(target, "PROVIDER_ERROR_LOG", tmp_path / "provider_error.log")
    monkeypatch.setattr(target.time, "sleep", waits.append)

    result = pi_session.send_prompt("hello", pid="42")

    assert result["data"]["text"] == "ok"
    assert waits == [2]
    assert calls[0] == ["send", "--pid", "42", "hello"]
    assert calls[1] == calls[0]
    assert calls[2] == ["send", "--pid", "42", "continue"]
    assert "provider timeout" in (
        tmp_path / "provider_error.log"
    ).read_text(encoding="utf-8")
