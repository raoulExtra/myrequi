"""Clarification-first safety gate for ambiguous or contradictory requests."""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from reasoning_trace import add_step, conclude, create_trace, ensure_schema as ensure_reasoning_trace_schema

ISSUE_TYPES = ("ambiguous", "contradictory", "missing_detail", "unsafe_assumption", "unclear_scope")
STATES = ("clarification_required", "assumption_proposed", "assumption_authorized", "resolved", "blocked", "safe_response_only")


def ensure_schema(conn) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS interaction_clarifications (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      original_input TEXT NOT NULL,
      normalized_input TEXT NOT NULL,
      issue_type TEXT NOT NULL CHECK(issue_type IN ('ambiguous','contradictory','missing_detail','unsafe_assumption','unclear_scope')),
      detection_method TEXT NOT NULL,
      materiality TEXT NOT NULL CHECK(materiality IN ('low','moderate','high','very-high')),
      risk_band TEXT NOT NULL CHECK(risk_band IN ('low','moderate','high','very-high')),
      candidates_json TEXT NOT NULL DEFAULT '[]',
      proposed_interpretation TEXT NOT NULL DEFAULT '',
      question TEXT NOT NULL,
      options_json TEXT NOT NULL DEFAULT '[]',
      state TEXT NOT NULL CHECK(state IN ('clarification_required','assumption_proposed','assumption_authorized','resolved','blocked','safe_response_only')),
      authorization TEXT NOT NULL DEFAULT 'none' CHECK(authorization IN ('none','explicit','assumed')),
      route_name TEXT,
      session_key TEXT,
      resolution_note TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      resolved_at TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_clarifications_active ON interaction_clarifications(state, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_clarifications_session ON interaction_clarifications(session_key, state);
    CREATE TABLE IF NOT EXISTS clarification_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      clarification_id INTEGER NOT NULL REFERENCES interaction_clarifications(id) ON DELETE CASCADE,
      event_type TEXT NOT NULL,
      payload_json TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_clarification_events_lookup ON clarification_events(clarification_id, created_at);
    CREATE VIEW IF NOT EXISTS clarification_active_flow AS
    SELECT id, original_input, normalized_input, issue_type, materiality, risk_band,
           candidates_json, proposed_interpretation, question, options_json,
           state, authorization, route_name, session_key, resolution_note,
           created_at, resolved_at
    FROM interaction_clarifications
    WHERE state IN ('clarification_required', 'assumption_proposed', 'assumption_authorized');
    CREATE VIEW IF NOT EXISTS clarification_event_lineage AS
    SELECT c.id AS clarification_id, c.state, c.authorization, c.route_name,
           e.id AS event_id, e.event_type, e.payload_json, e.created_at AS event_created_at
    FROM interaction_clarifications AS c
    LEFT JOIN clarification_events AS e ON e.clarification_id = c.id;
    CREATE TABLE IF NOT EXISTS clarification_trace_links (
      clarification_id INTEGER PRIMARY KEY REFERENCES interaction_clarifications(id) ON DELETE CASCADE,
      reasoning_trace_id INTEGER NOT NULL REFERENCES reasoning_traces(id) ON DELETE CASCADE,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_clarification_trace_links_trace ON clarification_trace_links(reasoning_trace_id);
    """)


def _materiality_score(issue_type: str, risk_band: str, candidates: list[str]) -> float:
    base = {"ambiguous": .80, "contradictory": .85, "missing_detail": .70,
            "unsafe_assumption": .95, "unclear_scope": .80}[issue_type]
    if risk_band == "very-high":
        base = max(base, .90)
    if len(candidates) >= 2:
        base = min(1.0, base + .05)
    return round(base, 2)


def _finding(issue_type: str, method: str, question: str, options: list[str], *, materiality: str = "high", risk_band: str = "high", candidates: Optional[list[str]] = None) -> dict[str, Any]:
    candidate_list = candidates or []
    return {"issue_type": issue_type, "detection_method": method, "materiality": materiality,
            "materiality_score": _materiality_score(issue_type, risk_band, candidate_list),
            "risk_band": risk_band, "candidates": candidate_list, "question": question,
            "options": options}


def classify_input(input_text: str, decision: Optional[dict[str, Any]] = None) -> Optional[dict[str, Any]]:
    """Return a finding only when ambiguity can materially change an action."""
    text = " ".join(str(input_text or "").split())
    lowered = text.lower()
    route_type = (decision or {}).get("route_type")
    route_name = (decision or {}).get("route_name")

    if re.search(r"\b(?:don't|do not|never)\b.*\b(?:and|then)\b.*\b(?:do|run|send|execute|delete|add)\b", lowered):
        return _finding("contradictory", "contradictory_instruction_markers",
                        "Which instruction is the current one?",
                        ["Keep the first instruction", "Keep the later instruction", "Neither—revise the request"],
                        candidates=["first instruction", "later instruction", "revised request"])

    safety_action_match = re.search(r"\b(?:prescribe|administer|take|change|stop|adjust)\b[^.!?]*\b(?:medication|medicine|dosage|dose|treatment|therapy)\b|\b(?:deploy|release|push|run|delete|overwrite)\b[^.!?]*\b(?:production|prod)\b", text, re.IGNORECASE)
    if safety_action_match:
        return _finding("unsafe_assumption", "high_impact_action_boundary",
                        "Should this remain advisory, or is a specific authorized action intended?",
                        ["Advisory information only—take no action", "Specify the authorized action and scope", "Cancel"],
                        risk_band="very-high", candidates=[safety_action_match.group(0).strip()])

    antecedent_match = re.search(r"\b(?:delete|remove|drop|truncate|destroy|overwrite|send|forward|share|message|update|modify|change|run)\b[^.!?]*\b(it|this|that|them|these|those)\b", text, re.IGNORECASE)
    if antecedent_match:
        return _finding("unclear_scope", "unresolved_antecedent",
                        "What exact target does the referenced item mean?",
                        ["Specify the exact target", "Inspect the possible target first", "Cancel"],
                        risk_band="very-high", candidates=[antecedent_match.group(1)])

    recipient_match = re.search(r"\b(?:to|recipient)\s+([^,;]+?)\s+(?:or|either)\s+([^,;]+)", text, re.IGNORECASE)
    if re.search(r"\b(?:send|forward|share|message)\b", lowered) and recipient_match:
        candidates = [recipient_match.group(1).strip(), recipient_match.group(2).strip()]
        return _finding("ambiguous", "multiple_recipient_candidates",
                        "Which single recipient or chat should receive this?",
                        candidates + ["Do not send anything"], risk_band="very-high", candidates=candidates)

    destructive_target_match = re.search(r"\b(?:delete|remove|drop|truncate|destroy|overwrite)\b\s+(.+?)\s+(?:or|either)\s+(.+?)(?:\s|$)", text, re.IGNORECASE)
    if destructive_target_match:
        candidates = [destructive_target_match.group(1).strip(), destructive_target_match.group(2).strip()]
        return _finding("ambiguous", "multiple_destructive_target_candidates",
                        "Which exact target should this affect?",
                        candidates + ["Preview only—make no change", "Cancel"], risk_band="very-high", candidates=candidates)

    if re.search(r"\b(?:send|forward|share|message)\b", lowered) and not re.search(r"\b(?:to|chat|recipient|@)\b", lowered):
        return _finding("missing_detail", "external_recipient_missing",
                        "Who is the intended recipient or chat?",
                        ["Specify a recipient", "Specify a Telegram chat", "Do not send anything"], risk_band="very-high")

    if re.search(r"\b(?:delete|remove|drop|truncate|destroy|overwrite)\b", lowered) and not re.search(r"\b(?:file|table|database|row|record|path|name)\b", lowered):
        return _finding("unclear_scope", "destructive_target_missing",
                        "What exact target should this affect?",
                        ["Specify the exact target", "Preview only—make no change", "Cancel"], risk_band="very-high")

    if lowered in {"git add", "git commit", "git push"} or (lowered.startswith("git add ") and lowered.endswith("?")):
        return _finding("missing_detail", "git_scope_missing",
                        "Which exact files or paths should be staged?",
                        ["Specify paths", "Stage all tracked changes", "Do not stage anything"], risk_band="high")

    if route_type in {"control_command", "agent_tool"} and not text:
        return _finding("missing_detail", "empty_action_input", "What exact action should be performed?",
                        ["Specify the action", "Inspect only", "Cancel"], risk_band="high")

    return None


def get_blocking_clarification(conn, session_key: Optional[str] = None):
    """Return one active clarification that must be resolved before another action."""
    if session_key is None:
        return None
    return conn.execute("SELECT * FROM interaction_clarifications WHERE state IN ('clarification_required', 'assumption_proposed') AND session_key=? ORDER BY id DESC LIMIT 10", (session_key,)).fetchone()


def get_active_clarification(conn, input_text: str, session_key: Optional[str] = None):
    normalized = " ".join(str(input_text or "").split())
    if session_key is None:
        return conn.execute(
            "SELECT * FROM interaction_clarifications WHERE normalized_input=? AND state='clarification_required' ORDER BY id DESC LIMIT 1",
            (normalized,),
        ).fetchone()
    return conn.execute(
        "SELECT * FROM interaction_clarifications WHERE normalized_input=? AND session_key=? AND state='clarification_required' ORDER BY id DESC LIMIT 1",
        (normalized, session_key),
    ).fetchone()


def answer_clarification(conn, clarification_id: int, answer: str, *, authorization: str = "none") -> dict[str, Any]:
    """Record an answer; only an explicit, non-cancel answer can resolve a clarification."""
    row = conn.execute("SELECT * FROM interaction_clarifications WHERE id=?", (clarification_id,)).fetchone()
    if row is None:
        return {"status": "not_found", "clarification_id": clarification_id}
    current = row["state"] if hasattr(row, "keys") else row[11]
    if current != "clarification_required":
        return {"status": "stale", "clarification_id": clarification_id, "state": current}
    text = " ".join(str(answer or "").split())
    lowered = text.lower()
    options = json.loads(row["options_json"] if hasattr(row, "keys") else row[10])
    selected = None
    match = re.match(r"^([1-9])(?:[.)]|\s|$)", text)
    if match and int(match.group(1)) <= len(options):
        selected = options[int(match.group(1)) - 1]
    contradictory_answer = bool(re.search(r"\b(?:yes\b.*\bno|no\b.*\byes)\b", lowered))
    if contradictory_answer:
        conn.execute("INSERT INTO clarification_events(clarification_id,event_type,payload_json) VALUES(?,?,?)",
                     (clarification_id, "contradictory_answer", json.dumps({"answer": text, "selected": selected})))
        trace_row = conn.execute("SELECT reasoning_trace_id FROM clarification_trace_links WHERE clarification_id=?", (clarification_id,)).fetchone()
        if trace_row:
            add_step(conn, trace_row[0], "observation", f"Contradictory clarification answer received: {text}")
        conn.commit()
        return {"status": "clarification_required", "clarification_id": clarification_id, "reasoning_trace_id": trace_row[0] if trace_row else None, "message": "The answer contains conflicting choices; please provide one clear answer."}
    partial_answer = selected is not None and any(selected.lower().startswith(prefix) for prefix in ("specify", "preview", "inspect"))
    if authorization == "explicit" and lowered.startswith("assume ") and text[7:].strip():
        state, auth = "assumption_authorized", "explicit"
    elif (selected is not None and any(token in selected.lower() for token in ("cancel", "do not", "neither"))) or (selected is None and lowered in {"cancel", "cancelled", "neither", "no", "do not", "don't"}):
        state, auth = "blocked", "none"
    elif authorization == "explicit" and text and not partial_answer:
        state, auth = "resolved", "explicit"
    else:
        conn.execute("INSERT INTO clarification_events(clarification_id,event_type,payload_json) VALUES(?,?,?)",
                     (clarification_id, "partial_answer" if partial_answer else "answer_received", json.dumps({"answer": text, "selected": selected})))
        trace_row = conn.execute("SELECT reasoning_trace_id FROM clarification_trace_links WHERE clarification_id=?", (clarification_id,)).fetchone()
        if trace_row:
            add_step(conn, trace_row[0], "observation", f"User answer received: {text}")
        conn.commit()
        return {"status": "clarification_required", "clarification_id": clarification_id, "reasoning_trace_id": trace_row[0] if trace_row else None, "message": "Answer recorded, but explicit authorization or a complete target is still required."}
    if state == "assumption_authorized":
        conn.execute("UPDATE interaction_clarifications SET state=?, authorization=?, proposed_interpretation=?, resolution_note=? WHERE id=?", (state, auth, text[7:].strip(), text, clarification_id))
        conn.execute("INSERT INTO clarification_events(clarification_id,event_type,payload_json) VALUES(?,?,?)", (clarification_id, "assumption_authorized", json.dumps({"assumption": text[7:].strip(), "authorization": auth})))
        conn.commit()
        return {"status": state, "clarification_id": clarification_id, "interpretation": text[7:].strip(), "authorization": auth}
    conn.execute("""UPDATE interaction_clarifications SET state=?, authorization=?, proposed_interpretation=?,
                    resolution_note=?, resolved_at=CURRENT_TIMESTAMP WHERE id=?""",
                 (state, auth, selected or text, text, clarification_id))
    conn.execute("INSERT INTO clarification_events(clarification_id,event_type,payload_json) VALUES(?,?,?)",
                 (clarification_id, "blocked" if state == "blocked" else "resolved",
                  json.dumps({"answer": text, "selected": selected, "authorization": auth})))
    trace_row = conn.execute("SELECT reasoning_trace_id FROM clarification_trace_links WHERE clarification_id=?", (clarification_id,)).fetchone()
    if trace_row:
        add_step(conn, trace_row[0], "revision", f"Clarification {state}: {selected or text}")
        conclude(conn, trace_row[0], f"Clarification {state}; consequential execution remains separately gated", confidence=0.95, status="provisional")
    conn.commit()
    return {"status": state, "clarification_id": clarification_id, "reasoning_trace_id": trace_row[0] if trace_row else None, "interpretation": selected or text, "authorization": auth}


def create_clarification(conn, input_text: str, finding: dict[str, Any], decision: Optional[dict[str, Any]] = None, session_key: Optional[str] = None) -> dict[str, Any]:
    """Persist one clarification and its detection event, idempotently for an active identical input."""
    normalized = " ".join(str(input_text or "").split())
    route_name = (decision or {}).get("route_name")
    row = get_active_clarification(conn, input_text, session_key=session_key)
    if row:
        clarification_id = row["id"] if hasattr(row, "keys") else row[0]
    else:
        cur = conn.execute("""INSERT INTO interaction_clarifications
          (original_input, normalized_input, issue_type, detection_method, materiality, risk_band,
           candidates_json, question, options_json, state, route_name, session_key)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'clarification_required', ?, ?)""",
          (str(input_text), normalized, finding["issue_type"], finding["detection_method"], finding["materiality"], finding["risk_band"],
           json.dumps(finding["candidates"]), finding["question"], json.dumps(finding["options"]), route_name, session_key))
        clarification_id = cur.lastrowid
        ensure_reasoning_trace_schema(conn)
        trace_id = create_trace(conn, f"clarification:{clarification_id}",
                                "Resolve the ambiguity before taking consequential action",
                                assumptions=["No consequential action is authorized while clarification is pending"],
                                uncertainty=finding["issue_type"])
        add_step(conn, trace_id, "decomposition", f"Detected {finding['issue_type']} via {finding['detection_method']}")
        add_step(conn, trace_id, "reason", finding["question"], confidence=0.9)
        add_step(conn, trace_id, "disconfirmation", "A complete target, scope, and authorization would remove this gate")
        conn.execute("INSERT INTO clarification_trace_links(clarification_id, reasoning_trace_id) VALUES(?,?)", (clarification_id, trace_id))
        conn.execute("INSERT INTO clarification_events(clarification_id,event_type,payload_json) VALUES(?,?,?)",
                     (clarification_id, "detected", json.dumps({**finding, "reasoning_trace_id": trace_id})))
        conn.commit()
    trace_row = conn.execute("SELECT reasoning_trace_id FROM clarification_trace_links WHERE clarification_id=?", (clarification_id,)).fetchone()
    return {"status": "clarification_required", "clarification_id": clarification_id,
            "reasoning_trace_id": trace_row[0] if trace_row else None,
            "issue_type": finding["issue_type"], "materiality": finding["materiality"],
            "risk_band": finding["risk_band"], "question": finding["question"],
            "options": finding["options"], "advisory_only": True}
