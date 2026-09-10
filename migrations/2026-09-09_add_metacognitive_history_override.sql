-- Add a deliberate, audited escape hatch for correcting immutable metacognitive history.
CREATE TABLE IF NOT EXISTS metacognitive_state_history_overrides (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  state_key TEXT NOT NULL,
  version INTEGER NOT NULL,
  authorized_by TEXT NOT NULL CHECK(length(trim(authorized_by)) > 0),
  reason TEXT NOT NULL CHECK(length(trim(reason)) > 0),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  consumed_at TEXT,
  UNIQUE(state_key, version, created_at)
);

CREATE TABLE IF NOT EXISTS metacognitive_state_history_override_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  override_id INTEGER NOT NULL REFERENCES metacognitive_state_history_overrides(id),
  state_key TEXT NOT NULL,
  version INTEGER NOT NULL,
  old_value TEXT NOT NULL,
  new_value TEXT NOT NULL,
  authorized_by TEXT NOT NULL,
  reason TEXT NOT NULL,
  changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DROP TRIGGER IF EXISTS metacognitive_state_history_no_update;
CREATE TRIGGER metacognitive_state_history_no_update
BEFORE UPDATE ON metacognitive_state_history
WHEN (NEW.state_key<>OLD.state_key OR NEW.category<>OLD.category OR NEW.value<>OLD.value
   OR NEW.confidence<>OLD.confidence OR NEW.provenance<>OLD.provenance OR NEW.version<>OLD.version)
 AND NOT EXISTS (
   SELECT 1 FROM metacognitive_state_history_overrides o
   WHERE o.state_key=OLD.state_key AND o.version=OLD.version AND o.consumed_at IS NULL
 )
BEGIN
  SELECT RAISE(ABORT, 'metacognitive_state_history is immutable; create an explicit override first');
END;

CREATE TRIGGER IF NOT EXISTS metacognitive_state_history_override_record
AFTER UPDATE ON metacognitive_state_history
WHEN (NEW.state_key<>OLD.state_key OR NEW.category<>OLD.category OR NEW.value<>OLD.value
   OR NEW.confidence<>OLD.confidence OR NEW.provenance<>OLD.provenance OR NEW.version<>OLD.version)
 AND EXISTS (
   SELECT 1 FROM metacognitive_state_history_overrides o
   WHERE o.state_key=OLD.state_key AND o.version=OLD.version AND o.consumed_at IS NULL
 )
BEGIN
  INSERT INTO metacognitive_state_history_override_audit
    (override_id,state_key,version,old_value,new_value,authorized_by,reason)
  SELECT o.id,OLD.state_key,OLD.version,OLD.value,NEW.value,o.authorized_by,o.reason
  FROM metacognitive_state_history_overrides o
  WHERE o.state_key=OLD.state_key AND o.version=OLD.version AND o.consumed_at IS NULL
  ORDER BY o.id LIMIT 1;

  UPDATE metacognitive_state_history_overrides
  SET consumed_at=CURRENT_TIMESTAMP
  WHERE id=(SELECT o.id FROM metacognitive_state_history_overrides o
            WHERE o.state_key=OLD.state_key AND o.version=OLD.version AND o.consumed_at IS NULL
            ORDER BY o.id LIMIT 1);
END;
