-- Consolidate legacy tool source history into the canonical code artifact model.
INSERT INTO code_artifacts (name, description, active_version)
SELECT DISTINCT
  t.tool_name,
  'Migrated from tool_source_versions; versioned source history.',
  MAX(t.version)
FROM tool_source_versions t
GROUP BY t.tool_name
ON CONFLICT(name) DO UPDATE SET
  active_version = MAX(code_artifacts.active_version, excluded.active_version),
  updated_at = CURRENT_TIMESTAMP;

INSERT OR IGNORE INTO code_versions
  (artifact_id, version, source, sha256, validation_status, validation_notes, approval_status)
SELECT
  ca.id,
  t.version,
  t.source,
  t.sha256,
  'passed',
  'Migrated from tool_source_versions; source and SHA-256 preserved.',
  'approved'
FROM tool_source_versions t
JOIN code_artifacts ca ON ca.name = t.tool_name;

DROP TABLE tool_source_versions;
