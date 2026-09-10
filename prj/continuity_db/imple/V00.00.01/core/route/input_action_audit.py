"""Audit and usage-recording helpers for routed actions."""

import json
import sqlite3
from typing import Any, Dict, Optional


def preview_text(value: Any, limit: int = 1000) -> Optional[str]:
    """Return a bounded, single-field text summary."""
    if value is None:
        return None
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except TypeError:
            text = str(value)
    text = text.strip()
    if len(text) > limit:
        return text[:limit] + "..."
    return text or None


def action_warning(action_result: Any) -> Optional[str]:
    if isinstance(action_result, dict):
        return preview_text(action_result.get("warning") or action_result.get("warnings"), 500)
    return None


def action_error(action_result: Any) -> Optional[str]:
    if isinstance(action_result, dict):
        return preview_text(action_result.get("error") or action_result.get("error_message"), 500)
    return None


def summarize_action_result(action_result: Any) -> Optional[str]:
    if isinstance(action_result, dict):
        for key in ("status", "message", "warning", "error", "value", "result", "assistant_text"):
            value = action_result.get(key)
            if value:
                return preview_text({key: value}, 2000)
    return preview_text(action_result, 2000)


def importance_reason(
    decision: Dict[str, Any],
    success: bool,
    action_result: Any,
    error_message: Optional[str],
) -> Optional[str]:
    """Return the reason an execution deserves a detailed receipt."""
    route_name = str(decision.get("route_name") or "unknown")
    if not success or error_message or action_error(action_result):
        return "error"
    if action_warning(action_result):
        return "warning"
    if route_name.startswith(("plan_", "receipt_", "promotion_", "hypothesis_", "evidence_")):
        return "state_or_audit_route"
    if route_name.startswith("memory_") and not route_name.startswith("memory_recall"):
        return "state_or_audit_route"
    if route_name in {"report_gap", "route_on", "route_off", "session_model_set"}:
        return "state_changing_route"
    return None


def record_route_usage(
    conn: sqlite3.Connection,
    decision: Dict[str, Any],
    input_text: str,
    timestamp: str,
    success: bool,
    action_result: Any,
    error_message: Optional[str],
) -> None:
    """Update aggregate usage statistics for one routed action."""
    route_name = str(decision.get("route_name") or "unmatched")
    route_type = str(decision.get("route_type") or "unknown")
    warning = action_warning(action_result)
    error = error_message or action_error(action_result)
    conn.execute(
        """
        INSERT INTO route_usage_stats (
            route_name, route_type, total_count, success_count, error_count, warning_count,
            first_used_at, last_used_at, last_success_at, last_error_at, last_warning_at,
            last_input_preview, last_result_preview, last_error
        ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(route_name, route_type) DO UPDATE SET
            total_count = total_count + 1,
            success_count = success_count + excluded.success_count,
            error_count = error_count + excluded.error_count,
            warning_count = warning_count + excluded.warning_count,
            last_used_at = excluded.last_used_at,
            last_success_at = COALESCE(excluded.last_success_at, route_usage_stats.last_success_at),
            last_error_at = COALESCE(excluded.last_error_at, route_usage_stats.last_error_at),
            last_warning_at = COALESCE(excluded.last_warning_at, route_usage_stats.last_warning_at),
            last_input_preview = excluded.last_input_preview,
            last_result_preview = excluded.last_result_preview,
            last_error = COALESCE(excluded.last_error, route_usage_stats.last_error)
        """,
        (
            route_name,
            route_type,
            1 if success else 0,
            0 if success else 1,
            1 if warning else 0,
            timestamp,
            timestamp,
            timestamp if success else None,
            timestamp if not success or error else None,
            timestamp if warning else None,
            preview_text(input_text, 500),
            summarize_action_result(action_result),
            error,
        ),
    )


def record_route_receipt(
    conn: sqlite3.Connection,
    decision: Dict[str, Any],
    input_text: str,
    timestamp: str,
    success: bool,
    action_result: Any,
    error_message: Optional[str],
    importance_reason: str,
    input_action_log_id: Optional[int] = None,
) -> None:
    """Write a detailed receipt for an important routed action."""
    conn.execute(
        """
        INSERT INTO route_execution_receipts (
            timestamp, route_name, route_type, input_text, success, importance_reason,
            result_summary, error_message, warning_message, decision_json, action_result_json,
            input_action_log_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            decision.get("route_name"),
            decision.get("route_type"),
            str(input_text),
            1 if success else 0,
            importance_reason,
            summarize_action_result(action_result),
            error_message or action_error(action_result),
            action_warning(action_result),
            preview_text(decision, 5000),
            preview_text(action_result, 5000),
            input_action_log_id,
        ),
    )
