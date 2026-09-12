-- Unify control-command and agent-tool route metadata.
CREATE TABLE IF NOT EXISTS command_routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_name TEXT NOT NULL UNIQUE,
    input_pattern TEXT NOT NULL,
    route_type TEXT NOT NULL DEFAULT 'control_command'
        CHECK(route_type IN ('control_command', 'agent_tool')),
    command_template TEXT,
    scope TEXT,
    handler TEXT,
    required_capability TEXT,
    output_contract TEXT,
    enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO command_routes
(route_name, input_pattern, route_type, command_template, scope, enabled)
SELECT route_name, input_pattern, 'control_command', command_template, scope, enabled
FROM control_command_routes;

INSERT OR IGNORE INTO command_routes
(route_name, input_pattern, route_type, handler, required_capability, output_contract, enabled)
SELECT route_name, input_pattern, 'agent_tool', handler, required_capability, output_contract, enabled
FROM agent_tool_routes;

DROP TABLE control_command_routes;
DROP TABLE agent_tool_routes;
