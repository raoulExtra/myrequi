-- Insert the set_phase command route
INSERT OR IGNORE INTO control_command_routes (route_name, input_pattern, command_template, scope, enabled)
VALUES (
  'set_phase',
  '{"type":"set_phase","project":"*PROJECT","phase":"*PHASE"}',
  'set_phase --project "*PROJECT" --phase "*PHASE"',
  'global',
  1
);
