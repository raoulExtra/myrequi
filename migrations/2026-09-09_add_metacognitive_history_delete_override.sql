-- Extend the explicit override mechanism to permit one audited history deletion.
ALTER TABLE metacognitive_state_history_overrides
  ADD COLUMN action TEXT NOT NULL DEFAULT 'update'
  CHECK(action IN ('update','delete'));

DROP TRIGGER IF EXISTS metacognitive_state_history_no_update;
CREATE TRIGGER metacognitive_state_history_no_update
BEFORE UPDATE ON metacognitive_state_history
WHEN (NEW.state_key<>OLD.state_key OR NEW.category<>OLD.category OR NEW.value<>OLD.value
   OR NEW.confidence<>OLD.confidence OR NEW.provenance<>OLD.provenance OR NEW.version<>OLD.version)
 AND NOT EXISTS (
   SELECT 1 FROM metacognitive_state_history_overrides o
   WHERE o.state_key=OLD.state_key AND o.version=OLD.version
     AND o.action='update' AND o.consumed_at IS NULL
 )
BEGIN
  SELECT RAISE(ABORT, 'metacognitive_state_history is immutable; create an explicit update override first');
END;

DROP TRIGGER IF EXISTS metacognitive_state_history_no_delete;
CREATE TRIGGER metacognitive_state_history_no_delete
BEFORE DELETE ON metacognitive_state_history
WHEN NOT EXISTS (
  SELECT 1 FROM metacognitive_state_history_overrides o
  WHERE o.state_key=OLD.state_key AND o.version=OLD.version
    AND o.action='delete' AND o.consumed_at IS NULL
)
BEGIN
  SELECT RAISE(ABORT, 'metacognitive_state_history is immutable; create an explicit delete override first');
END;

DROP TRIGGER IF EXISTS metacognitive_state_history_override_record;
CREATE TRIGGER metacognitive_state_history_override_record
AFTER UPDATE ON metacognitive_state_history
WHEN (NEW.state_key<>OLD.state_key OR NEW.category<>OLD.category OR NEW.value<>OLD.value
   OR NEW.confidence<>OLD.confidence OR NEW.provenance<>OLD.provenance OR NEW.version<>OLD.version)
 AND EXISTS (
   SELECT 1 FROM metacognitive_state_history_overrides o
   WHERE o.state_key=OLD.state_key AND o.version=OLD.version
     AND o.action='update' AND o.consumed_at IS NULL
 )
BEGIN
  INSERT INTO metacognitive_state_history_override_audit
    (override_id,state_key,version,old_value,new_value,authorized_by,reason)
  SELECT o.id,OLD.state_key,OLD.version,OLD.value,NEW.value,o.authorized_by,o.reason
  FROM metacognitive_state_history_overrides o
  WHERE o.state_key=OLD.state_key AND o.version=OLD.version
    AND o.action='update' AND o.consumed_at IS NULL
  ORDER BY o.id LIMIT 1;
  UPDATE metacognitive_state_history_overrides SET consumed_at=CURRENT_TIMESTAMP
  WHERE id=(SELECT o.id FROM metacognitive_state_history_overrides o
            WHERE o.state_key=OLD.state_key AND o.version=OLD.version
              AND o.action='update' AND o.consumed_at IS NULL
            ORDER BY o.id LIMIT 1);
END;

CREATE TRIGGER metacognitive_state_history_delete_override_record
AFTER DELETE ON metacognitive_state_history
WHEN EXISTS (
  SELECT 1 FROM metacognitive_state_history_overrides o
  WHERE o.state_key=OLD.state_key AND o.version=OLD.version
    AND o.action='delete' AND o.consumed_at IS NULL
)
BEGIN
  INSERT INTO metacognitive_state_history_override_audit
    (override_id,state_key,version,old_value,new_value,authorized_by,reason)
  SELECT o.id,OLD.state_key,OLD.version,OLD.value,'[DELETED]',o.authorized_by,o.reason
  FROM metacognitive_state_history_overrides o
  WHERE o.state_key=OLD.state_key AND o.version=OLD.version
    AND o.action='delete' AND o.consumed_at IS NULL
  ORDER BY o.id LIMIT 1;
  UPDATE metacognitive_state_history_overrides SET consumed_at=CURRENT_TIMESTAMP
  WHERE id=(SELECT o.id FROM metacognitive_state_history_overrides o
            WHERE o.state_key=OLD.state_key AND o.version=OLD.version
              AND o.action='delete' AND o.consumed_at IS NULL
            ORDER BY o.id LIMIT 1);
END;
