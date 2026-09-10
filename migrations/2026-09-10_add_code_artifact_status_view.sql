-- Provide one comparable status surface for executable artifacts and extensions.
DROP VIEW IF EXISTS v_code_artifact_status;

CREATE VIEW v_code_artifact_status AS
SELECT
  ca.id AS artifact_id,
  ca.name,
  ca.description,
  ca.active_version,
  cv.validation_status,
  cv.approval_status,
  cv.sha256,
  COALESCE(
    group_concat(DISTINCT ot.tag_key),
    ''
  ) AS current_tags,
  ca.created_at,
  ca.updated_at
FROM code_artifacts ca
LEFT JOIN code_versions cv
  ON cv.artifact_id = ca.id
 AND cv.version = ca.active_version
LEFT JOIN object_epistemic_tags ot
  ON ot.object_type = 'row'
 AND ot.object_key = 'code_artifacts:name=' || ca.name
GROUP BY
  ca.id,
  ca.name,
  ca.description,
  ca.active_version,
  cv.validation_status,
  cv.approval_status,
  cv.sha256,
  ca.created_at,
  ca.updated_at;
