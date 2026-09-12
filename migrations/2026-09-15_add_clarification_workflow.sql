-- Clarification-first workflow. Detection is persisted; unresolved requests cannot authorize execution.
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
