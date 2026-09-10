-- Add route-recognition mode and its control routes.
INSERT INTO feature_flags (feature_key, enabled, switchable, scope, updated_by)
VALUES (
  'route_mode',
  0,
  1,
  'Route-recognition mode for matching routes in normal chat input.',
  'system'
)
ON CONFLICT(feature_key) DO UPDATE SET
  switchable=excluded.switchable,
  scope=excluded.scope;

INSERT INTO metacognitive_state (state_key, category, value, confidence, provenance, version)
VALUES (
  'active_route_mode',
  'modes',
  'general',
  1.0,
  'system',
  1
)
ON CONFLICT(state_key) DO UPDATE SET
  category=excluded.category,
  value=excluded.value,
  confidence=excluded.confidence,
  provenance=excluded.provenance;

INSERT INTO control_command_routes (route_name, input_pattern, command_template, scope, enabled)
VALUES
  (
    'route_on',
    '^(?:mode\\s+)?route(?:\\s+mode)?\\s+on$',
    'python3 mode_command.py route on --db continuity.db',
    'Enable route-recognition mode so normal chat can match routes.',
    1
  ),
  (
    'route_off',
    '^(?:mode\\s+)?route(?:\\s+mode)?\\s+off$',
    'python3 mode_command.py route off --db continuity.db',
    'Disable route-recognition mode so normal chat is treated as plain chat.',
    1
  ),
  (
    'route_status',
    '^(?:mode\\s+)?route(?:\\s+mode)?\\s+status$',
    'python3 mode_command.py route status --db continuity.db',
    'Show route-recognition mode status.',
    1
  )
ON CONFLICT(route_name) DO UPDATE SET
  input_pattern=excluded.input_pattern,
  command_template=excluded.command_template,
  scope=excluded.scope,
  enabled=1;
