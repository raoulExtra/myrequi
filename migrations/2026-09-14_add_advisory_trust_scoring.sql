-- Advisory-only trust assessments. This stores recommendations, never execution permission.
CREATE TABLE IF NOT EXISTS trust_advisory_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL CHECK(domain IN ('medical_advice','high_impact_software')),
    risk REAL NOT NULL CHECK(risk BETWEEN 0 AND 1),
    quality REAL NOT NULL CHECK(quality BETWEEN 0 AND 1),
    provenance REAL NOT NULL CHECK(provenance BETWEEN 0 AND 1),
    domain_fit REAL NOT NULL CHECK(domain_fit BETWEEN 0 AND 1),
    freshness REAL NOT NULL CHECK(freshness BETWEEN 0 AND 1),
    conflict REAL NOT NULL DEFAULT 0 CHECK(conflict BETWEEN 0 AND 1),
    base_confidence REAL NOT NULL CHECK(base_confidence BETWEEN 0 AND 1),
    adjusted_confidence REAL NOT NULL CHECK(adjusted_confidence BETWEEN 0 AND 1),
    posture TEXT NOT NULL CHECK(posture IN ('allow','caution','verify','review','defer')),
    advisory_only INTEGER NOT NULL DEFAULT 1 CHECK(advisory_only=1),
    failed_floors_json TEXT NOT NULL DEFAULT '[]',
    uncertainty_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_trust_advisory_domain_risk
    ON trust_advisory_assessments(domain, risk, created_at DESC);

CREATE TABLE IF NOT EXISTS trust_advisory_pilot_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_json TEXT NOT NULL,
    results_json TEXT NOT NULL,
    advisory_only INTEGER NOT NULL DEFAULT 1 CHECK(advisory_only=1),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO command_routes(route_name, input_pattern, route_type, command_template, scope, output_contract, enabled)
VALUES (
    'trust_assess',
    '^trust\s+assess\s+(medical_advice|high_impact_software)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)$',
    'control_command',
    'trust assess <domain> <Q> <P> <D> <F> <R>',
    'Advisory-only trust assessment; never authorizes execution.',
    'JSON posture, scores, failed floors, and uncertainty.',
    1
)
ON CONFLICT(route_name) DO UPDATE SET
    input_pattern=excluded.input_pattern,
    command_template=excluded.command_template,
    scope=excluded.scope,
    output_contract=excluded.output_contract,
    enabled=1;
