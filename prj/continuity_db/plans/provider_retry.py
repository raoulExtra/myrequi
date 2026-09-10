"""Retry policy for transient LLM provider errors."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from time import sleep
from typing import TypeVar


Result = TypeVar("Result")


def _log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} | {message}\n")


def request_with_retry(
    request: Callable[[], Result],
    *,
    provider: str,
    error_log: Path,
    sleep_fn: Callable[[float], None] = sleep,
    continue_fn: Callable[[], None] | None = None,
) -> Result:
    """Run a provider request, retry once after two seconds, then continue.

    The second provider failure is re-raised after the continue callback runs.
    The callback is injectable so orchestration and tests can define what
    issuing ``continue`` means without invoking a shell command here.
    """
    had_provider_error = False
    for attempt in (1, 2):
        try:
            result = request()
        except Exception as error:
            had_provider_error = True
            _log(
                error_log,
                f"provider={provider} event=provider_error attempt={attempt} "
                f"error={error}",
            )
            if attempt == 2:
                if continue_fn is not None:
                    _log(error_log, f"provider={provider} event=continue")
                    continue_fn()
                raise
            _log(error_log, f"provider={provider} event=wait seconds=2")
            sleep_fn(2)
            _log(error_log, f"provider={provider} event=retry attempt=2")
        else:
            if had_provider_error and continue_fn is not None:
                _log(error_log, f"provider={provider} event=continue")
                continue_fn()
            return result

    raise RuntimeError("provider retry loop ended unexpectedly")
