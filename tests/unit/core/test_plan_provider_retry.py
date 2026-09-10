from pathlib import Path

import pytest

from prj.continuity_db.plans.provider_retry import request_with_retry


def test_provider_error_waits_two_seconds_logs_and_continues(tmp_path: Path):
    attempts = []
    waits = []
    continued = []

    def request():
        attempts.append(1)
        if len(attempts) == 1:
            raise RuntimeError("temporary provider failure")
        return "accepted response"

    result = request_with_retry(
        request,
        provider="test-provider",
        error_log=tmp_path / "provider_error.log",
        sleep_fn=waits.append,
        continue_fn=lambda: continued.append(True),
    )

    assert result == "accepted response"
    assert len(attempts) == 2
    assert waits == [2]
    assert continued == [True]

    log = (tmp_path / "provider_error.log").read_text(encoding="utf-8")
    assert "test-provider" in log
    assert "temporary provider failure" in log
    assert "retry" in log
    assert "continue" in log


def test_second_provider_error_is_raised_after_continue(tmp_path: Path):
    continued = []

    def request():
        raise RuntimeError("provider unavailable")

    with pytest.raises(RuntimeError, match="provider unavailable"):
        request_with_retry(
            request,
            provider="test-provider",
            error_log=tmp_path / "provider_error.log",
            sleep_fn=lambda seconds: None,
            continue_fn=lambda: continued.append(True),
        )

    assert continued == [True]
    log = (tmp_path / "provider_error.log").read_text(encoding="utf-8")
    assert log.count("provider unavailable") == 2
