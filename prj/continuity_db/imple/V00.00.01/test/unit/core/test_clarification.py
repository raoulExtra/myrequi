import sqlite3

from clarification import classify_input, create_clarification, ensure_schema


def test_missing_git_scope_requires_clarification():
    finding = classify_input("git add")
    assert finding["issue_type"] == "missing_detail"
    assert finding["risk_band"] == "high"


def test_send_without_recipient_requires_clarification():
    finding = classify_input("send continuity.db")
    assert finding["issue_type"] == "missing_detail"
    assert finding["risk_band"] == "very-high"


def test_contradiction_requires_clarification():
    finding = classify_input("do not send it and then send it")
    assert finding["issue_type"] == "contradictory"


def test_safe_unmatched_text_is_not_blocked():
    assert classify_input("What is the current project status?") is None


def test_persistence_is_idempotent_for_active_input():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    finding = classify_input("git add")
    first = create_clarification(conn, "git add", finding)
    second = create_clarification(conn, "git add", finding)
    assert first["clarification_id"] == second["clarification_id"]
    assert conn.execute("SELECT COUNT(*) FROM interaction_clarifications").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM clarification_events").fetchone()[0] == 1
