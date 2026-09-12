"""Inspectable reasoning summaries and intermediate steps.

This stores concise, reviewable reasoning artifacts, not private chain-of-thought.
"""
from __future__ import annotations

import json
from typing import Any, Iterable, Optional

STEP_TYPES = {"decomposition", "assumption", "observation", "claim", "reason",
              "alternative", "disconfirmation", "interface", "verification", "revision"}
STATUSES = {"open", "provisional", "verified", "revised", "closed"}


def ensure_schema(conn) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS reasoning_traces (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      trace_key TEXT NOT NULL UNIQUE,
      question TEXT NOT NULL,
      conclusion TEXT NOT NULL DEFAULT '',
      confidence REAL CHECK(confidence IS NULL OR confidence BETWEEN 0 AND 1),
      uncertainty TEXT NOT NULL DEFAULT '',
      status TEXT NOT NULL CHECK(status IN ('open','provisional','verified','revised','closed')) DEFAULT 'open',
      assumptions_json TEXT NOT NULL DEFAULT '[]',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS reasoning_trace_steps (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      trace_id INTEGER NOT NULL REFERENCES reasoning_traces(id) ON DELETE CASCADE,
      step_order INTEGER NOT NULL,
      step_type TEXT NOT NULL CHECK(step_type IN ('decomposition','assumption','observation','claim','reason','alternative','disconfirmation','interface','verification','revision')),
      summary TEXT NOT NULL,
      confidence REAL CHECK(confidence IS NULL OR confidence BETWEEN 0 AND 1),
      evidence_json TEXT NOT NULL DEFAULT '[]',
      depends_on_json TEXT NOT NULL DEFAULT '[]',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(trace_id, step_order)
    );
    CREATE INDEX IF NOT EXISTS idx_reasoning_traces_status ON reasoning_traces(status, updated_at DESC);
    CREATE INDEX IF NOT EXISTS idx_reasoning_trace_steps_trace ON reasoning_trace_steps(trace_id, step_order);
    CREATE TABLE IF NOT EXISTS reasoning_trace_reviews (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      trace_id INTEGER NOT NULL REFERENCES reasoning_traces(id) ON DELETE CASCADE,
      review_kind TEXT NOT NULL CHECK(review_kind IN ('premise_check','verification','context_audit')),
      verdict TEXT NOT NULL CHECK(verdict IN ('pass','revise','blocked','inconclusive')),
      findings_json TEXT NOT NULL DEFAULT '[]',
      checked_assumptions_json TEXT NOT NULL DEFAULT '[]',
      context_budget_note TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_reasoning_trace_reviews_trace ON reasoning_trace_reviews(trace_id, created_at DESC);
    """)


def create_trace(conn, trace_key: str, question: str, *, assumptions: Optional[Iterable[str]] = None,
                 uncertainty: str = "", confidence: Optional[float] = None) -> int:
    if confidence is not None and not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    row = conn.execute("SELECT id FROM reasoning_traces WHERE trace_key=?", (trace_key,)).fetchone()
    if row:
        return row[0]
    cur = conn.execute("""INSERT INTO reasoning_traces
        (trace_key, question, assumptions_json, uncertainty, confidence)
        VALUES (?, ?, ?, ?, ?)""",
        (trace_key, question, json.dumps(list(assumptions or [])), uncertainty, confidence))
    conn.commit()
    return cur.lastrowid


def add_step(conn, trace_id: int, step_type: str, summary: str, *,
             evidence: Optional[Iterable[Any]] = None, depends_on: Optional[Iterable[int]] = None,
             confidence: Optional[float] = None) -> int:
    if step_type not in STEP_TYPES:
        raise ValueError(f"unsupported step_type: {step_type}")
    if confidence is not None and not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    prior = conn.execute("SELECT COALESCE(MAX(step_order), 0) FROM reasoning_trace_steps WHERE trace_id=?", (trace_id,)).fetchone()[0]
    cur = conn.execute("""INSERT INTO reasoning_trace_steps
        (trace_id, step_order, step_type, summary, confidence, evidence_json, depends_on_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (trace_id, prior + 1, step_type, summary, confidence,
         json.dumps(list(evidence or [])), json.dumps(list(depends_on or []))))
    conn.execute("UPDATE reasoning_traces SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (trace_id,))
    conn.commit()
    return cur.lastrowid


def add_assumption(conn, trace_id: int, assumption: str) -> None:
    row = conn.execute("SELECT assumptions_json FROM reasoning_traces WHERE id=?", (trace_id,)).fetchone()
    if row is None:
        raise ValueError("trace not found")
    assumptions = json.loads(row[0])
    if assumption not in assumptions:
        assumptions.append(assumption)
    conn.execute("UPDATE reasoning_traces SET assumptions_json=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (json.dumps(assumptions), trace_id))
    conn.commit()


def attach_evidence(conn, trace_id: int, step_order: int, evidence: Any) -> None:
    row = conn.execute("SELECT evidence_json FROM reasoning_trace_steps WHERE trace_id=? AND step_order=?", (trace_id, step_order)).fetchone()
    if row is None:
        raise ValueError("reasoning step not found")
    items = json.loads(row[0])
    items.append(evidence)
    conn.execute("UPDATE reasoning_trace_steps SET evidence_json=? WHERE trace_id=? AND step_order=?", (json.dumps(items), trace_id, step_order))
    conn.execute("UPDATE reasoning_traces SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (trace_id,))
    conn.commit()


def conclude(conn, trace_id: int, conclusion: str, *, confidence: float,
             uncertainty: str = "", status: str = "provisional") -> None:
    if status not in STATUSES:
        raise ValueError(f"unsupported status: {status}")
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    conn.execute("""UPDATE reasoning_traces
        SET conclusion=?, confidence=?, uncertainty=?, status=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?""", (conclusion, confidence, uncertainty, status, trace_id))
    conn.commit()


def update_uncertainty(conn, trace_id: int, confidence: float, note: str) -> None:
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if not note.strip():
        raise ValueError("uncertainty note is required")
    cur = conn.execute("UPDATE reasoning_traces SET confidence=?, uncertainty=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (confidence, note, trace_id))
    if cur.rowcount == 0:
        raise ValueError("trace not found")
    conn.commit()


def add_review(conn, trace_id: int, review_kind: str, verdict: str, *,
               findings: Optional[Iterable[str]] = None,
               checked_assumptions: Optional[Iterable[str]] = None,
               context_budget_note: str = "") -> int:
    if review_kind not in {"premise_check", "verification", "context_audit"}:
        raise ValueError(f"unsupported review_kind: {review_kind}")
    if verdict not in {"pass", "revise", "blocked", "inconclusive"}:
        raise ValueError(f"unsupported verdict: {verdict}")
    cur = conn.execute("""INSERT INTO reasoning_trace_reviews
        (trace_id, review_kind, verdict, findings_json, checked_assumptions_json, context_budget_note)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (trace_id, review_kind, verdict, json.dumps(list(findings or [])),
         json.dumps(list(checked_assumptions or [])), context_budget_note))
    status = "verified" if verdict == "pass" else "revised" if verdict == "revise" else "open"
    conn.execute("UPDATE reasoning_traces SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, trace_id))
    conn.commit()
    return cur.lastrowid


def audit_trace(conn, trace_id: int) -> dict[str, Any]:
    result = inspect_trace(conn, trace_id)
    if result.get("status") == "not_found":
        return result
    types = {step["type"] for step in result["steps"]}
    reviews = result.get("reviews", [])
    checks = {
        "decomposed": "decomposition" in types,
        "assumptions_explicit": bool(result.get("assumptions")) or "assumption" in types,
        "alternative_considered": "alternative" in types,
        "disconfirmation_attempted": "disconfirmation" in types,
        "uncertainty_stated": bool(result.get("uncertainty")),
        "conclusion_recorded": bool(result.get("conclusion")),
        "verification_reviewed": any(r["kind"] == "verification" for r in reviews),
        "verification_passed": any(r["kind"] == "verification" and r["verdict"] == "pass" for r in reviews),
    }
    return {"trace_id": trace_id, "checks": checks,
            "missing": [name for name, passed in checks.items() if not passed],
            "ready_to_finalize": all(checks.values())}


def ready_to_finalize(conn, trace_id: int) -> bool:
    audit = audit_trace(conn, trace_id)
    return bool(audit.get("ready_to_finalize"))


def finalize_trace(conn, trace_id: int) -> None:
    """Close a trace only after a conclusion and a passing verification review exist."""
    if not ready_to_finalize(conn, trace_id):
        raise ValueError("cannot finalize without a conclusion and passing verification review")
    conn.execute("UPDATE reasoning_traces SET status='closed', updated_at=CURRENT_TIMESTAMP WHERE id=?", (trace_id,))
    conn.commit()


def inspect_trace(conn, trace_id: int) -> dict[str, Any]:
    trace = conn.execute("SELECT * FROM reasoning_traces WHERE id=?", (trace_id,)).fetchone()
    if trace is None:
        return {"status": "not_found", "trace_id": trace_id}
    steps = conn.execute("SELECT step_order, step_type, summary, confidence, evidence_json, depends_on_json FROM reasoning_trace_steps WHERE trace_id=? ORDER BY step_order", (trace_id,)).fetchall()
    return {"trace_id": trace_id, "trace_key": trace["trace_key"] if hasattr(trace, "keys") else trace[1],
            "question": trace["question"] if hasattr(trace, "keys") else trace[2],
            "conclusion": trace["conclusion"] if hasattr(trace, "keys") else trace[3],
            "confidence": trace["confidence"] if hasattr(trace, "keys") else trace[4],
            "uncertainty": trace["uncertainty"] if hasattr(trace, "keys") else trace[5],
            "status": trace["status"] if hasattr(trace, "keys") else trace[6],
            "assumptions": json.loads(trace["assumptions_json"] if hasattr(trace, "keys") else trace[7]),
            "steps": [{"order": r[0], "type": r[1], "summary": r[2], "confidence": r[3],
                       "evidence": json.loads(r[4]), "depends_on": json.loads(r[5])} for r in steps],
            "reviews": [{"kind": r[0], "verdict": r[1], "findings": json.loads(r[2]),
                         "checked_assumptions": json.loads(r[3]), "context_budget_note": r[4]} for r in conn.execute(
                             "SELECT review_kind, verdict, findings_json, checked_assumptions_json, context_budget_note FROM reasoning_trace_reviews WHERE trace_id=? ORDER BY id", (trace_id,)).fetchall()]}
