"""Deterministic llm-guard stand-in for content-guard unit tests.

This mock never imports llm-guard, downloads models, or requires its virtual
environment. Tests may configure a pass, denial, sanitization, or exception.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MockScanner:
    """Small scanner double matching llm-guard's ``scan`` shape."""

    name: str = "mock-scanner"
    valid: bool = True
    sanitized_text: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    error: Exception | None = None
    calls: list[str] = field(default_factory=list)

    def scan(self, text: str) -> tuple[str, bool]:
        self.calls.append(text)
        if self.error is not None:
            raise self.error
        return self.sanitized_text if self.sanitized_text is not None else text, self.valid

    @property
    def result(self) -> dict[str, Any]:
        return {
            "scanner": self.name,
            "is_valid": self.valid,
            "details": self.details,
        }


@dataclass
class MockGuard:
    """Collection of configured scanners used by adapter tests."""

    scanners: list[MockScanner] = field(default_factory=list)

    def scan(self, text: str) -> tuple[str, bool, list[dict[str, Any]]]:
        current = text
        results = []
        valid = True
        for scanner in self.scanners:
            current, scanner_valid = scanner.scan(current)
            valid = valid and scanner_valid
            results.append(scanner.result)
        return current, valid, results


def passing_scanner(name: str = "mock-pass") -> MockScanner:
    return MockScanner(name=name)


def denying_scanner(
    name: str = "mock-deny", *, reason: str = "mock denial"
) -> MockScanner:
    return MockScanner(name=name, valid=False, details={"reason": reason})


def failing_scanner(
    name: str = "mock-error", *, message: str = "mock scanner failure"
) -> MockScanner:
    return MockScanner(name=name, error=RuntimeError(message))
