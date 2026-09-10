"""Database schema and migration helpers for the continuity database router."""

import sqlite3


def ensure_router_schema(conn: sqlite3.Connection) -> None:
    """Create router-owned tables and apply compatible evidence migrations."""
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS input_action_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            input_text TEXT NOT NULL,
            input_type TEXT NOT NULL,
            matched_route_name TEXT,
            matched_route_type TEXT,
            action_type TEXT NOT NULL,
            parameters TEXT,
            success INTEGER NOT NULL,
            error_message TEXT,
            planning_episode_id INTEGER,
            loop_iteration INTEGER DEFAULT 0,
            FOREIGN KEY (planning_episode_id) REFERENCES work_plans(id)
        );
        CREATE TABLE IF NOT EXISTS input_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_name TEXT NOT NULL UNIQUE,
            pattern_type TEXT NOT NULL CHECK(pattern_type IN ('json_path', 'json_value', 'json_regex')),
            pattern_spec TEXT NOT NULL,
            route_name TEXT NOT NULL,
            route_type TEXT NOT NULL CHECK(route_type IN ('control_command', 'agent_tool')),
            priority INTEGER NOT NULL DEFAULT 0,
            description TEXT,
            enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
            pending_route INTEGER NOT NULL DEFAULT 0 CHECK(pending_route IN (0,1)),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS route_usage_stats (
            route_name TEXT NOT NULL,
            route_type TEXT NOT NULL,
            total_count INTEGER NOT NULL DEFAULT 0,
            success_count INTEGER NOT NULL DEFAULT 0,
            error_count INTEGER NOT NULL DEFAULT 0,
            warning_count INTEGER NOT NULL DEFAULT 0,
            first_used_at TEXT,
            last_used_at TEXT,
            last_success_at TEXT,
            last_error_at TEXT,
            last_warning_at TEXT,
            last_input_preview TEXT,
            last_result_preview TEXT,
            last_error TEXT,
            PRIMARY KEY (route_name, route_type)
        );
        CREATE TABLE IF NOT EXISTS route_execution_receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            route_name TEXT,
            route_type TEXT,
            input_text TEXT NOT NULL,
            success INTEGER NOT NULL,
            importance_reason TEXT NOT NULL,
            result_summary TEXT,
            error_message TEXT,
            warning_message TEXT,
            decision_json TEXT,
            action_result_json TEXT,
            input_action_log_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS promotion_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,
            source_id INTEGER,
            candidate_kind TEXT NOT NULL,
            reason TEXT NOT NULL,
            summary TEXT NOT NULL,
            score REAL NOT NULL DEFAULT 0.5,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','promoted','rejected')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            promoted_to_type TEXT,
            promoted_to_id TEXT,
            promoted_at TEXT,
            UNIQUE(source_type, source_id, candidate_kind)
        );
        CREATE TABLE IF NOT EXISTS hypotheses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hypothesis_key TEXT NOT NULL UNIQUE,
            claim TEXT NOT NULL,
            prediction TEXT NOT NULL DEFAULT '',
            expected_evidence TEXT NOT NULL DEFAULT '',
            falsifier TEXT NOT NULL DEFAULT '',
            confidence REAL NOT NULL DEFAULT 0.5,
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','supported','weakened','falsified','retired')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS evidence_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL DEFAULT 'user_observation',
            source_ref TEXT,
            source_actor TEXT NOT NULL DEFAULT 'unknown',
            provenance_json TEXT NOT NULL DEFAULT '',
            observation TEXT NOT NULL,
            reliability REAL NOT NULL DEFAULT 0.7,
            recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS hypothesis_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hypothesis_id INTEGER NOT NULL,
            evidence_id INTEGER NOT NULL,
            relation TEXT NOT NULL CHECK(relation IN ('supports','weakens','neutral','falsifies')),
            rationale TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(hypothesis_id, evidence_id),
            FOREIGN KEY(hypothesis_id) REFERENCES hypotheses(id),
            FOREIGN KEY(evidence_id) REFERENCES evidence_ledger(id)
        );
        CREATE TABLE IF NOT EXISTS belief_confidence_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_type TEXT NOT NULL CHECK(target_type IN ('hypothesis','belief')),
            target_id INTEGER NOT NULL,
            confidence_before REAL,
            confidence_after REAL NOT NULL,
            reason TEXT NOT NULL,
            evidence_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    migrate_evidence_ledger(cur)


def migrate_evidence_ledger(cur: sqlite3.Cursor) -> None:
    """Add provenance columns required by the scientific evidence layer."""
    for ddl in (
        "ALTER TABLE evidence_ledger ADD COLUMN source_actor TEXT NOT NULL DEFAULT 'unknown'",
        "ALTER TABLE evidence_ledger ADD COLUMN provenance_json TEXT NOT NULL DEFAULT ''",
    ):
        try:
            cur.execute(ddl)
        except sqlite3.OperationalError:
            # The column already exists when the migration has run previously.
            pass
