-- Add a route for prompting the live Pi session bridge.
INSERT OR IGNORE INTO control_command_routes (route_name, input_pattern, command_template, scope, enabled)
VALUES (
  'session_prompt',
  '^session\\s+prompt\\s+(.+)$',
  'python3 pi_session.py <prompt>',
  'Prompt the live Pi session bridge and return the bridge state plus send response.',
  1
);
