import sqlite3

import pytest

from reasoning_trace import add_assumption, add_review, add_step, attach_evidence, conclude, create_trace, ensure_schema, finalize_trace, inspect_trace, ready_to_finalize, update_uncertainty


def test_trace_exposes_steps_evidence_assumptions_and_uncertainty():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    trace_id = create_trace(conn, "demo-1", "Which action is safe?",
                            assumptions=["target is non-production"],
                            uncertainty="target environment not independently verified", confidence=.55)
    first = add_step(conn, trace_id, "decomposition", "Separate target selection from authorization", confidence=.9)
    add_step(conn, trace_id, "alternative", "Read-only inspection", evidence=["existing route metadata"], depends_on=[first], confidence=.7)
    add_step(conn, trace_id, "disconfirmation", "A production target would invalidate the low-risk assumption")
    conclude(conn, trace_id, "Inspect first; do not mutate yet", confidence=.8, status="provisional")
    result = inspect_trace(conn, trace_id)
    assert result["status"] == "provisional"
    assert result["assumptions"] == ["target is non-production"]
    assert len(result["steps"]) == 3
    assert result["steps"][1]["depends_on"] == [first]


def test_uncertainty_requires_note_and_updates_confidence():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    trace_id = create_trace(conn, "uncertainty-1", "How certain is this?")
    update_uncertainty(conn, trace_id, .35, "Only indirect evidence; alternative explanations remain")
    result = inspect_trace(conn, trace_id)
    assert result["confidence"] == .35
    assert "alternative" in result["uncertainty"]
    with pytest.raises(ValueError):
        update_uncertainty(conn, trace_id, .35, "")


def test_assumptions_are_explicit_and_deduplicated():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    trace_id = create_trace(conn, "assumption-1", "What is assumed?")
    add_assumption(conn, trace_id, "The target is non-production")
    add_assumption(conn, trace_id, "The target is non-production")
    assert inspect_trace(conn, trace_id)["assumptions"] == ["The target is non-production"]


def test_evidence_attaches_to_specific_step():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    trace_id = create_trace(conn, "evidence-1", "What supports this?")
    add_step(conn, trace_id, "claim", "The target is safe")
    attach_evidence(conn, trace_id, 1, {"source": "test", "fact": "read-only"})
    assert inspect_trace(conn, trace_id)["steps"][0]["evidence"] == [{"source": "test", "fact": "read-only"}]


def test_verification_review_is_separate_and_changes_status():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    trace_id = create_trace(conn, "review-1", "Is the premise valid?")
    add_step(conn, trace_id, "assumption", "The supplied target exists")
    add_review(conn, trace_id, "premise_check", "revise",
               findings=["Target existence is unverified"],
               checked_assumptions=["The supplied target exists"],
               context_budget_note="Kept only target and authorization context")
    result = inspect_trace(conn, trace_id)
    assert result["status"] == "revised"
    assert result["reviews"][0]["verdict"] == "revise"
    assert result["reviews"][0]["findings"] == ["Target existence is unverified"]


def test_finalization_requires_verification_pass():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    trace_id = create_trace(conn, "final-1", "Can this be finalized?", assumptions=["Input is complete"], uncertainty="Evidence is limited")
    add_step(conn, trace_id, "decomposition", "Separate premise from conclusion")
    add_step(conn, trace_id, "alternative", "Consider the opposite answer")
    add_step(conn, trace_id, "disconfirmation", "Look for evidence that would overturn it")
    conclude(conn, trace_id, "Provisional answer", confidence=.6, uncertainty="Evidence remains limited")
    assert not ready_to_finalize(conn, trace_id)
    with pytest.raises(ValueError):
        finalize_trace(conn, trace_id)
    add_review(conn, trace_id, "verification", "pass", findings=["No logical leap found"])
    assert ready_to_finalize(conn, trace_id)
    finalize_trace(conn, trace_id)
    assert inspect_trace(conn, trace_id)["status"] == "closed"


def test_trace_keys_are_idempotent_and_validation_is_strict():
    conn = sqlite3.connect(":memory:")
    ensure_schema(conn)
    first = create_trace(conn, "same", "question")
    assert create_trace(conn, "same", "different question") == first
    with pytest.raises(ValueError):
        add_step(conn, first, "guess", "opaque leap")
    with pytest.raises(ValueError):
        conclude(conn, first, "bad confidence", confidence=1.2)
