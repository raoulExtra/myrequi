-- Link material clarifications to concise inspectable reasoning traces.
CREATE TABLE IF NOT EXISTS clarification_trace_links (
  clarification_id INTEGER PRIMARY KEY REFERENCES interaction_clarifications(id) ON DELETE CASCADE,
  reasoning_trace_id INTEGER NOT NULL REFERENCES reasoning_traces(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_clarification_trace_links_trace ON clarification_trace_links(reasoning_trace_id);
