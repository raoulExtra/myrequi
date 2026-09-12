-- Insert the set_phase command route
INSERT OR IGNORE INTO command_routes (route_name, input_pattern, route_type, command_template, scope, enabled)
VALUES (
  'set_phase',
  '{"type":"set_phase","project":"*PROJECT","phase":"*PHASE"}',
  'control_command',
  'set_phase --project "*PROJECT" --phase "*PHASE"',
  'global',
  1
);
