-- Add routes for the live Pi session bridge.
INSERT OR IGNORE INTO control_command_routes (route_name, input_pattern, command_template, scope, enabled)
VALUES (
  'session_prompt',
  '^(?:session\\s+prompt|p)\\s+(.+)$',
  'python3 pi_session.py <prompt>',
  'Prompt the live Pi session bridge and return the bridge state plus send response.',
  1
);

INSERT OR IGNORE INTO control_command_routes (route_name, input_pattern, command_template, scope, enabled)
VALUES (
  'session_latest_answer',
  '^(?:pi_session\\.latest_assistant_text|latest\\s+answer|latest\\s+assistant\\s+text)(?:\\s*\\(\\s*pid\\s*=\\s*"?([^\\)"\\']+)"?\\s*\\))?$',
  'python3 -c "import pi_session; print(pi_session.latest_assistant_text(pid=<pid>))"',
  'Return the latest assistant text from the live Pi session bridge.',
  1
);
