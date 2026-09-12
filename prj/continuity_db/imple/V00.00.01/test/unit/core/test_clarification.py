import sqlite3

from clarification import answer_clarification, classify_input, create_clarification, ensure_schema, get_blocking_clarification


def test_missing_git_scope_requires_clarification():
    finding = classify_input("git add")
    assert finding["issue_type"] == "missing_detail"
    assert finding["risk_band"] == "high"


def test_send_without_recipient_requires_clarification():
    finding = classify_input("send continuity.db")
    assert finding["issue_type"] == "missing_detail"
    assert finding["risk_band"] == "very-high"


def test_high_impact_action_boundary_requires_clarification():
    finding = classify_input("deploy the release to production")
    assert finding["issue_type"] == "unsafe_assumption"
    assert finding["detection_method"] == "high_impact_action_boundary"
    assert finding["risk_band"] == "very-high"
    assert finding["materiality_score"] == .95


def test_unresolved_antecedent_requires_clarification():
    finding = classify_input("delete it")
    assert finding["issue_type"] == "unclear_scope"
    assert finding["detection_method"] == "unresolved_antecedent"
    assert finding["risk_band"] == "very-high"
    assert finding["materiality_score"] == .90


def test_multiple_recipients_require_clarification():
    finding = classify_input("send report.txt to @alice or @bob")
    assert finding["issue_type"] == "ambiguous"
    assert finding["detection_method"] == "multiple_recipient_candidates"
    assert finding["risk_band"] == "very-high"
    assert len(finding["candidates"]) == 2


def test_multiple_destructive_targets_require_clarification():
    finding = classify_input("delete file-a.txt or file-b.txt")
    assert finding["issue_type"] == "ambiguous"
    assert finding["detection_method"] == "multiple_destructive_target_candidates"
    assert finding["risk_band"] == "very-high"


def test_contradiction_requires_clarification():
    finding = classify_input("do not send it and then send it")
    assert finding["issue_type"] == "contradictory"


def test_safe_unmatched_text_is_not_blocked():
    assert classify_input("What is the current project status?") is None


def test_contradictory_answer_remains_unresolved():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    created = create_clarification(conn, "send continuity.db", classify_input("send continuity.db"))
    result = answer_clarification(conn, created["clarification_id"], "yes, send it; no, do not send it", authorization="explicit")
    assert result["status"] == "clarification_required"
    assert conn.execute("SELECT state FROM interaction_clarifications").fetchone()[0] == "clarification_required"
    assert conn.execute("SELECT event_type FROM clarification_events ORDER BY id DESC LIMIT 1").fetchone()[0] == "contradictory_answer"


def test_partial_answer_stays_unresolved_even_with_authorization():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    created = create_clarification(conn, "git add", classify_input("git add"))
    result = answer_clarification(conn, created["clarification_id"], "1", authorization="explicit")
    assert result["status"] == "clarification_required"
    assert conn.execute("SELECT event_type FROM clarification_events ORDER BY id DESC LIMIT 1").fetchone()[0] == "partial_answer"


def test_explicit_assumption_authorization_is_not_resolution():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    created = create_clarification(conn, "git add", classify_input("git add"))
    result = answer_clarification(conn, created["clarification_id"], "assume all tracked files", authorization="explicit")
    assert result["status"] == "assumption_authorized"
    assert conn.execute("SELECT state FROM interaction_clarifications").fetchone()[0] == "assumption_authorized"


def test_answer_requires_explicit_authorization_and_then_resolves():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    finding = classify_input("send continuity.db")
    created = create_clarification(conn, "send continuity.db", finding)
    pending = answer_clarification(conn, created["clarification_id"], "@peter")
    assert pending["status"] == "clarification_required"
    resolved = answer_clarification(conn, created["clarification_id"], "@peter", authorization="explicit")
    assert resolved["status"] == "resolved"
    assert conn.execute("SELECT state FROM interaction_clarifications").fetchone()[0] == "resolved"
    trace_id = conn.execute("SELECT reasoning_trace_id FROM clarification_trace_links").fetchone()[0]
    assert conn.execute("SELECT COUNT(*) FROM reasoning_trace_steps WHERE trace_id=?", (trace_id,)).fetchone()[0] == 5


def test_cancel_blocks_and_later_answer_is_stale():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    finding = classify_input("git add")
    created = create_clarification(conn, "git add", finding)
    blocked = answer_clarification(conn, created["clarification_id"], "3")
    assert blocked["status"] == "blocked"
    assert answer_clarification(conn, created["clarification_id"], "src/app.py", authorization="explicit")["status"] == "stale"


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
    trace_id = conn.execute("SELECT reasoning_trace_id FROM clarification_trace_links").fetchone()[0]
    assert trace_id is not None
    assert conn.execute("SELECT COUNT(*) FROM reasoning_trace_steps WHERE trace_id=?", (trace_id,)).fetchone()[0] == 3


def test_active_clarification_blocks_new_consequential_session_action():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    created = create_clarification(conn, "git add", classify_input("git add"), session_key="session-1")
    blocking = get_blocking_clarification(conn, "session-1")
    assert blocking["id"] == created["clarification_id"]
    assert get_blocking_clarification(conn, "session-2") is None


def test_clarification_views_expose_active_and_event_lineage():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    finding = classify_input("git add")
    created = create_clarification(conn, "git add", finding)
    active = conn.execute("SELECT id, state FROM clarification_active_flow WHERE id=?", (created["clarification_id"],)).fetchone()
    lineage = conn.execute("SELECT clarification_id, event_type FROM clarification_event_lineage WHERE clarification_id=? LIMIT 10", (created["clarification_id"],)).fetchall()
    assert active["id"] == created["clarification_id"]
    assert lineage and lineage[0]["clarification_id"] == created["clarification_id"]
