-- Add placeholder tag and demo link to a code_artifact
INSERT OR IGNORE INTO epistemic_tags (tag_key, label, description)
VALUES (
  'placeholder_needs_pull',
  'Placeholder — needs file pull',
  'Code artifact/version is a placeholder stub; actual implementation needs to be pulled from the filesystem or external source.'
);

-- Example: tag artifact with id=1 as placeholder (remove/adjust as needed)
-- INSERT OR IGNORE INTO object_epistemic_tags (object_type, object_key, tag_key, note)
-- VALUES ('code_artifact', '1', 'placeholder_needs_pull', 'Stub — pull from filesystem to complete');
