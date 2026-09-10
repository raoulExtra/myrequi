"""Optional, dependency-free-at-import adapter for llm-guard scanners.

The core can import this module without installing llm-guard. Scanner instances
are injectable so unit tests can use deterministic doubles and production can
use the isolated llm-guard environment.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Iterable


class GuardUnavailable(RuntimeError):
    """Raised only when a required guard cannot be constructed."""


def build_default_scanners() -> list[Any] | None:
    """Build the optional default scanner set, or return ``None`` if absent."""
    try:
        from llm_guard.input_scanners import PromptInjection
    except (ImportError, ModuleNotFoundError):
        return None

    try:
        return [PromptInjection()]
    except Exception:
        return None


def _scanner_name(scanner: Any) -> str:
    return str(getattr(scanner, "name", scanner.__class__.__name__))


def _provenance(
    text: str,
    scanners: Iterable[Any],
    source_url: str,
    source_title: str,
    guard_available: bool,
) -> dict[str, Any]:
    return {
        "guard": "llm-guard",
        "guard_available": guard_available,
        "scanners": [_scanner_name(scanner) for scanner in scanners],
        "source_url": source_url,
        "source_title": source_title,
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }


def _unavailable_decision(text: str, required: bool, source_url: str, source_title: str):
    return {
        "allowed": not required,
        "class": "blocked_guard_unavailable" if required else "guard_unavailable",
        "reason": "required content guard unavailable" if required else "optional content guard unavailable",
        "text": text,
        "provenance": _provenance(text, [], source_url, source_title, False),
    }


def scan_with_optional_guard(
    text: str,
    *,
    scanners: Iterable[Any] | None = None,
    required: bool = False,
    source_url: str = "",
    source_title: str = "",
) -> dict[str, Any]:
    """Scan content and return a safe decision plus non-content provenance.

    A missing optional dependency is tolerated. A required guard, scanner
    rejection, or scanner exception is denied rather than silently accepted.
    Retrieved content is returned only for the caller; it is never included in
    provenance metadata.
    """
    scanner_list = list(scanners) if scanners is not None else build_default_scanners()
    if scanner_list is None:
        return _unavailable_decision(text, required, source_url, source_title)

    current = text
    results = []
    provenance = _provenance(text, scanner_list, source_url, source_title, True)
    try:
        for scanner in scanner_list:
            current, valid = scanner.scan(current)
            result = getattr(scanner, "result", {})
            results.append(result if isinstance(result, dict) else {"result": result})
            if not valid:
                reason = "scanner rejected content"
                details = result.get("details", {}) if isinstance(result, dict) else {}
                if isinstance(details, dict) and details.get("reason"):
                    reason = str(details["reason"])
                return {
                    "allowed": False,
                    "class": "blocked_guard",
                    "reason": reason,
                    "text": current,
                    "scanner_results": results,
                    "provenance": provenance,
                }
    except Exception as exc:
        return {
            "allowed": False,
            "class": "blocked_guard_error",
            "reason": f"content guard scanner failed: {exc}",
            "text": text,
            "scanner_results": results,
            "provenance": provenance,
        }

    return {
        "allowed": True,
        "class": "guarded" if scanner_list else "guard_unavailable",
        "reason": "",
        "text": current,
        "scanner_results": results,
        "provenance": provenance,
    }
