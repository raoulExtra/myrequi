-- Add active_phase to projects (1=Frame, 2=Elicit, 3=Analyze, 4=Specify, 5=Validate, 6=Manage)
ALTER TABLE projects ADD COLUMN active_phase INTEGER NOT NULL DEFAULT 1 CHECK(active_phase BETWEEN 1 AND 6);

-- Optional: audit trail for phase changes (mirrors project_activation_events pattern)
CREATE TABLE IF NOT EXISTS project_phase_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  previous_phase INTEGER CHECK(previous_phase BETWEEN 1 AND 6),
  new_phase INTEGER NOT NULL CHECK(new_phase BETWEEN 1 AND 6),
  changed_by TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_project_phase_events_project ON project_phase_events(project_id, created_at DESC);

CREATE TRIGGER IF NOT EXISTS projects_phase_audit AFTER UPDATE OF active_phase ON projects
 WHEN OLD.active_phase <> NEW.active_phase
 BEGIN
   INSERT INTO project_phase_events(project_id, previous_phase, new_phase, changed_by, reason)
   VALUES (NEW.id, OLD.active_phase, NEW.active_phase, NEW.updated_by, 'Project phase change');
 END;
