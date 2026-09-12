-- Dedicated verification pass for inspectable reasoning traces.
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
