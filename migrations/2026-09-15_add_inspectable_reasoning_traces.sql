-- Concise, inspectable reasoning structure; never store hidden chain-of-thought.
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
CREATE VIEW IF NOT EXISTS inspectable_reasoning_flow AS
SELECT t.id AS trace_id, t.trace_key, t.question, t.conclusion, t.confidence,
       t.uncertainty, t.status, t.assumptions_json,
       s.step_order, s.step_type, s.summary, s.confidence AS step_confidence,
       s.evidence_json, s.depends_on_json
FROM reasoning_traces t
LEFT JOIN reasoning_trace_steps s ON s.trace_id=t.id
ORDER BY t.id, s.step_order;
