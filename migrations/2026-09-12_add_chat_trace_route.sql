-- Add a safe, completed-event trace route for message-adapter delivery.
INSERT OR IGNORE INTO feature_flags(feature_key, enabled, switchable, scope, updated_by)
VALUES('chat_trace_auto', 0, 1, 'delivery', 'system');

INSERT INTO command_routes
(route_name, input_pattern, route_type, command_template, scope, enabled)
VALUES
(
    'chat_trace',
    '^chat\\s+trace(?:\\s+since\\s+(\\S+))?(?:\\s+--pid\\s+(\\S+))?$',
    'control_command',
    'python3 -c "import pi_session; print(pi_session.chat_trace())"',
    'session',
    1
)
ON CONFLICT(route_name) DO UPDATE SET
    input_pattern=excluded.input_pattern,
    command_template=excluded.command_template,
    scope=excluded.scope,
    enabled=1;

INSERT INTO command_routes
(route_name, input_pattern, route_type, command_template, scope, enabled)
VALUES
('chat_trace_telegram', '^chat\\s+trace\\s+telegram(?:\\s+since\\s+(\\S+))?(?:\\s+--pid\\s+(\\S+))?$', 'control_command', 'telegram send latest completed chat trace', 'session', 1)
ON CONFLICT(route_name) DO UPDATE SET
    input_pattern=excluded.input_pattern,
    command_template=excluded.command_template,
    scope=excluded.scope,
    enabled=1;

INSERT INTO command_routes
(route_name, input_pattern, route_type, command_template, scope, enabled)
VALUES
('chat_trace_status', '^chat\\s+trace\\s+status$', 'control_command', 'show chat trace delivery status', 'session', 1)
ON CONFLICT(route_name) DO UPDATE SET
    input_pattern=excluded.input_pattern,
    command_template=excluded.command_template,
    scope=excluded.scope,
    enabled=1;

INSERT INTO command_routes
(route_name, input_pattern, route_type, command_template, scope, enabled)
VALUES
('chat_trace_auto', '^chat\\s+trace\\s+auto\\s+(on|off|status)$', 'control_command', 'set chat trace automatic delivery <action>', 'delivery', 1)
ON CONFLICT(route_name) DO UPDATE SET
    input_pattern=excluded.input_pattern,
    command_template=excluded.command_template,
    scope=excluded.scope,
    enabled=1;

INSERT INTO command_routes
(route_name, input_pattern, route_type, command_template, scope, enabled)
VALUES
('extension_status', '^(?:extension|extensions)\\s+status$', 'control_command', 'show active extensions and versions', 'extension', 1)
ON CONFLICT(route_name) DO UPDATE SET
    input_pattern=excluded.input_pattern,
    command_template=excluded.command_template,
    scope=excluded.scope,
    enabled=1;

UPDATE command_routes
SET input_pattern='^(?:chat\\s+latest|pi_session\\.latest_assistant_text|latest\\s+answer|latest\\s+assistant\\s+text)(?:\\s*\\(\\s*pid\\s*=\\s*"?([^\\)"'']+)"?\\s*\\))?$'
WHERE route_name='session_latest_answer';
