#!/usr/bin/env python3
"""Continuous input action router with JSON pattern matching and loop planning.

This module continuously reads user input, uses JSON pattern matching to decide what
engine action or trigger should happen, and supports loop planning workflows.
It integrates with the existing continuity.db routing system (control_command_routes
and agent_tool_routes) and supports both immediate actions and iterative planning.

Usage:
    python3 input_action_router.py --continuous
    python3 input_action_router.py --loop
    python3 input_action_router.py --single <user_input>
"""

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from input_action_database import migrate_evidence_ledger
from input_action_matching import (
    build_routing_indexes,
    literal_prefix,
    match_json_pattern,
    match_routing_rule,
    pattern_prefixes,
    route_candidates_for_text,
)
from input_action_parsing import parse_input

U_ACTION = "uaction"

ROOT = Path(__file__).resolve().parents[5]
DB_PATH = ROOT / "continuity.db"
PLANS_DIR = ROOT / "plans"


class InputActionRouter:
    """Continuous input action router with JSON pattern matching."""

    def __init__(self, db_path: Path = DB_PATH, pid: Optional[str] = None, verbose: bool = True):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys=ON')
        self.pid = pid
        self.verbose = verbose
        self.setup_database()
        self.running = False
        self.loop_mode = False
        self.current_plan = None
        self._routing_rules_cache: Optional[List[Dict[str, Any]]] = None
        self._routing_buckets_cache: Optional[Dict[str, List[Dict[str, Any]]]] = None
        self._routing_fallback_cache: Optional[List[Dict[str, Any]]] = None
        self._route_lookup_cache: Optional[Dict[str, Dict[str, Any]]] = None

    def setup_database(self):
        """Ensure required tables and views exist; seed patterns from existing routes."""
        cur = self.conn.cursor()

        # Create input_action_log table for audit trail
        cur.execute("""
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
            )
        """)

        # Create input_patterns table for JSON pattern matching rules
        cur.execute("""
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
            )
        """)

        # Compact aggregate stats: one row per route instead of one row per routine call.
        cur.execute("""
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
            )
        """)

        # Detailed receipts are reserved for important events only: errors,
        # warnings, state-changing route classes, or explicit receipt-worthy routes.
        cur.execute("""
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
            )
        """)

        # Promotion candidates are the metabolism layer between cheap traces and
        # durable memory objects.  Candidate rows are small, reviewable, and can
        # be promoted into memory_fragments or reasoning_episodes.
        cur.execute("""
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
            )
        """)

        # Scientific layer: separate hypotheses from evidence, predictions,
        # falsifiers, and confidence updates.
        cur.execute("""
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
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS evidence_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL DEFAULT 'user_observation',
                source_ref TEXT,
                source_actor TEXT NOT NULL DEFAULT 'unknown',
                provenance_json TEXT NOT NULL DEFAULT '',
                observation TEXT NOT NULL,
                reliability REAL NOT NULL DEFAULT 0.7,
                recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        migrate_evidence_ledger(cur)
        cur.execute("""
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
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS belief_confidence_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_type TEXT NOT NULL CHECK(target_type IN ('hypothesis','belief')),
                target_id INTEGER NOT NULL,
                confidence_before REAL,
                confidence_after REAL NOT NULL,
                reason TEXT NOT NULL,
                evidence_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()
        self._seed_science_routes()
        self._seed_promotion_routes()
        self.seed_patterns_from_routes()
        self.setup_views()

    def _seed_science_routes(self):
        """Install built-in scientific-method commands if absent."""
        cur = self.conn.cursor()
        routes = [
            (
                "hypothesis_add",
                r"^hypothesis\s+add\s+(.+?)\s+predicts\s+(.+?)\s+falsifier\s+(.+)$",
                "hypothesis add <claim> predicts <prediction> falsifier <falsifier>",
                "Create a testable hypothesis with prediction and falsifier.",
            ),
            (
                "hypothesis_list",
                r"^(hypothesis\s+list|hypotheses)$",
                "hypothesis list",
                "List active hypotheses.",
            ),
            (
                "evidence_add",
                r"^evidence\s+add\s+hypothesis\s+(\d+)\s+(supports|weakens|neutral|falsifies)\s+(.+?)\s+source\s+(.+)$",
                "evidence add hypothesis <id> <relation> <observation> source <source>",
                "Add evidence and link it to a hypothesis.",
            ),
            (
                "hypothesis_test",
                r"^(?:test\s+hypothesis|hypothesis\s+test)\s+(\d+)$",
                "test hypothesis <id>",
                "Show prediction, falsifier, and linked evidence for a hypothesis.",
            ),
            (
                "hypothesis_confidence_update",
                r"^hypothesis\s+update\s+(\d+)\s+confidence\s+([01](?:\.\d+)?)\s+because\s+(.+)$",
                "hypothesis update <id> confidence <0-1> because <reason>",
                "Record an auditable hypothesis confidence update.",
            ),
        ]
        for route_name, pattern, command_template, scope in routes:
            cur.execute("""
                INSERT INTO control_command_routes (route_name, input_pattern, command_template, scope, enabled)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(route_name) DO UPDATE SET
                    input_pattern=excluded.input_pattern,
                    command_template=excluded.command_template,
                    scope=excluded.scope,
                    enabled=1
            """, (route_name, pattern, command_template, scope))
        self.conn.commit()
        self._invalidate_routing_cache()

    def _seed_promotion_routes(self):
        """Install built-in promotion commands if they are absent."""
        cur = self.conn.cursor()
        routes = [
            (
                "promotion_candidate_add",
                r"^promote\s+candidate\s+(route_receipt|receipt)\s+(\d+)\s+to\s+(fragment|memory_fragment|reasoning_episode)\s+because\s+(.+)$",
                "promote candidate <source> <id> to <kind> because <reason>",
                "Create a pending promotion candidate from a route receipt.",
            ),
            (
                "promotion_list",
                r"^(promote\s+list|promotion\s+candidates|promotions)$",
                "promote list",
                "List pending promotion candidates.",
            ),
            (
                "promotion_apply",
                r"^promote\s+(\d+)(?:\s+to\s+(fragment|memory_fragment|reasoning_episode))?$",
                "promote <candidate_id> [to <kind>]",
                "Promote a candidate into a durable memory object.",
            ),
            (
                "promotion_reject",
                r"^promote\s+reject\s+(\d+)(?:\s+because\s+(.+))?$",
                "promote reject <candidate_id> [because <reason>]",
                "Reject a promotion candidate.",
            ),
        ]
        for route_name, pattern, command_template, scope in routes:
            cur.execute("""
                INSERT INTO control_command_routes (route_name, input_pattern, command_template, scope, enabled)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(route_name) DO UPDATE SET
                    input_pattern=excluded.input_pattern,
                    command_template=excluded.command_template,
                    scope=excluded.scope,
                    enabled=1
            """, (route_name, pattern, command_template, scope))
        self.conn.commit()
        self._invalidate_routing_cache()

    def seed_patterns_from_routes(self):
        """Seed input_patterns rows from existing enabled routes.
        Patterns are disabled (pending_route=1) if the route is missing.
        """
        cur = self.conn.cursor()

        # Auto-seed from control_command_routes
        try:
            control_routes = cur.execute(
                "SELECT route_name, input_pattern FROM control_command_routes WHERE enabled=1"
            ).fetchall()
            for row in control_routes:
                self._ensure_pattern_for_route(
                    pattern_name=f"auto_{row['route_name']}",
                    route_name=row['route_name'],
                    route_type='control_command',
                    pattern_spec=row['input_pattern'],
                    pattern_type='json_regex',
                )
        except sqlite3.OperationalError:
            pass

        # Auto-seed from agent_tool_routes
        try:
            agent_routes = cur.execute(
                "SELECT route_name, input_pattern FROM agent_tool_routes WHERE enabled=1"
            ).fetchall()
            for row in agent_routes:
                self._ensure_pattern_for_route(
                    pattern_name=f"auto_{row['route_name']}",
                    route_name=row['route_name'],
                    route_type='agent_tool',
                    pattern_spec=row['input_pattern'],
                    pattern_type='json_regex',
                )
        except sqlite3.OperationalError:
            pass

        self.conn.commit()
        self._invalidate_routing_cache()

    def _ensure_pattern_for_route(self, pattern_name, route_name, route_type, pattern_spec, pattern_type='json_regex'):
        """Insert a pattern row if missing; mark pending_route=1 if the route does not exist."""
        cur = self.conn.cursor()
        if route_type == 'control_command':
            exists = cur.execute(
                "SELECT 1 FROM control_command_routes WHERE route_name=? AND enabled=1",
                (route_name,),
            ).fetchone()
        else:
            exists = cur.execute(
                "SELECT 1 FROM agent_tool_routes WHERE route_name=? AND enabled=1",
                (route_name,),
            ).fetchone()

        pending_route = 0 if exists else 1
        enabled = 0 if pending_route else 1

        cur.execute("""
            INSERT INTO input_patterns
                (pattern_name, pattern_type, pattern_spec, route_name, route_type, priority, description, enabled, pending_route)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
            ON CONFLICT(pattern_name) DO UPDATE SET
                route_name=excluded.route_name,
                route_type=excluded.route_type,
                pattern_spec=excluded.pattern_spec,
                pending_route=excluded.pending_route,
                enabled=excluded.enabled,
                updated_at=CURRENT_TIMESTAMP
        """, (
            pattern_name, pattern_type, pattern_spec, route_name, route_type,
            f"Auto-seeded from {route_type}",
            enabled, pending_route,
        ))

    def add_route_if_missing(self, route_name, route_type, input_pattern, command_template=None, handler=None):
        """Create a route in the proper table if it does not exist; then enable its pattern."""
        cur = self.conn.cursor()
        if route_type == 'control_command':
            if not cur.execute("SELECT 1 FROM control_command_routes WHERE route_name=?", (route_name,)).fetchone():
                cur.execute("""
                    INSERT INTO control_command_routes (route_name, input_pattern, command_template, scope, enabled)
                    VALUES (?, ?, ?, 'auto_added', 1)
                """, (route_name, input_pattern, command_template or f"echo no-command-for-{route_name}"))
        elif route_type == 'agent_tool':
            if not cur.execute("SELECT 1 FROM agent_tool_routes WHERE route_name=?", (route_name,)).fetchone():
                cur.execute("""
                    INSERT INTO agent_tool_routes (route_name, input_pattern, handler, required_capability, output_contract, enabled)
                    VALUES (?, ?, ?, 'auto', 'json', 1)
                """, (route_name, input_pattern, handler or f"auto_handler_{route_name}"))
        self.conn.commit()
        # Re-evaluate pending patterns for this route_name
        cur.execute("""
            UPDATE input_patterns
            SET pending_route=0, enabled=1, updated_at=CURRENT_TIMESTAMP
            WHERE route_name=? AND route_type=? AND pending_route=1
        """, (route_name, route_type))
        self.conn.commit()
        self._invalidate_routing_cache()

    # --- topic helpers (using identity table) ---

    def set_topic(self, key, value, keep_version=True):
        """Set a topic value in the identity table without bumping version.
        If keep_version is True and the row exists, only value/updated_at change.
        If False, the version increments by 1 (auditable).
        """
        cur = self.conn.cursor()
        existing = cur.execute("SELECT version FROM identity WHERE key=?", (key,)).fetchone()
        if existing is None:
            cur.execute(
                "INSERT INTO identity (key, value, version) VALUES (?, ?, 1)",
                (key, value),
            )
        else:
            if keep_version:
                cur.execute(
                    "UPDATE identity SET value=?, updated_at=CURRENT_TIMESTAMP WHERE key=?",
                    (value, key),
                )
            else:
                cur.execute(
                    "UPDATE identity SET value=?, version=version+1, updated_at=CURRENT_TIMESTAMP WHERE key=?",
                    (value, key),
                )
        self.conn.commit()
        return cur.execute("SELECT key, value, version, updated_at FROM identity WHERE key=?", (key,)).fetchone()

    def get_topic(self, key, default=None):
        cur = self.conn.cursor()
        row = cur.execute("SELECT value, version FROM identity WHERE key=?", (key,)).fetchone()
        if row is None:
            return default
        return {"value": row[0], "version": row[1]}

    def list_topics(self, prefix=None):
        cur = self.conn.cursor()
        if prefix:
            rows = cur.execute(
                "SELECT key, value, version, updated_at FROM identity WHERE key LIKE ? ORDER BY key",
                (f"{prefix}%",),
            ).fetchall()
        else:
            rows = cur.execute(
                "SELECT key, value, version, updated_at FROM identity ORDER BY key"
            ).fetchall()
        return [dict(r) for r in rows]

    def setup_views(self):
        """Create useful views for the router."""
        cur = self.conn.cursor()
        
        # View for input routing decisions
        cur.execute("""
            CREATE VIEW IF NOT EXISTS v_input_routing AS
            SELECT 
                ial.id,
                ial.timestamp,
                ial.input_text,
                ial.input_type,
                ial.matched_route_name,
                ial.matched_route_type,
                ial.action_type,
                ial.parameters,
                ial.success,
                ial.error_message,
                ial.planning_episode_id,
                ial.loop_iteration,
                p.pattern_name as pattern_used
            FROM input_action_log ial
            LEFT JOIN input_patterns p ON 
                (ial.matched_route_name = p.route_name AND p.enabled = 1)
            ORDER BY ial.timestamp DESC
        """)
        
        # View for active routing patterns (only resolved, non-pending)
        cur.execute("""
            CREATE VIEW IF NOT EXISTS v_active_routing_patterns AS
            SELECT
                ip.id,
                ip.pattern_name,
                ip.pattern_type,
                ip.pattern_spec,
                ip.route_name,
                ip.route_type,
                ip.priority,
                ip.description,
                CASE
                    WHEN ip.route_type = 'control_command' THEN c.route_name
                    WHEN ip.route_type = 'agent_tool' THEN a.route_name
                    ELSE NULL
                END as target_route_name
            FROM input_patterns ip
            LEFT JOIN control_command_routes c ON c.route_name = ip.route_name AND c.enabled = 1
            LEFT JOIN agent_tool_routes a ON a.route_name = ip.route_name AND a.enabled = 1
            WHERE ip.enabled = 1 AND ip.pending_route = 0
            ORDER BY ip.priority DESC, ip.pattern_name
        """)
        
        self.conn.commit()

    def json_pattern_match(self, input_data: Union[str, Dict, Any], pattern_spec: str,
                           pattern_type: str) -> Tuple[bool, Dict[str, Any]]:
        """Match input against a JSON pattern using the matching module."""
        return match_json_pattern(input_data, pattern_spec, pattern_type)

    def _match_json_path(self, data: Dict, path_spec: str) -> Tuple[bool, Dict[str, Any]]:
        """Match using a JSON path pattern."""
        return match_json_pattern(data, path_spec, "json_path")

    def _match_json_value(self, data: Dict, value_spec: str) -> Tuple[bool, Dict[str, Any]]:
        """Match using a JSON value pattern."""
        return match_json_pattern(data, value_spec, "json_value")

    def _match_json_regex(self, data: Dict, regex_pattern: str) -> Tuple[bool, Dict[str, Any]]:
        """Match using a JSON regex pattern."""
        return match_json_pattern(data, regex_pattern, "json_regex")

    def load_routing_rules(self) -> List[Dict[str, Any]]:
        """Load active, resolved routing patterns (enabled=1, pending_route=0)."""
        if self._routing_rules_cache is not None:
            return self._routing_rules_cache
        try:
            rows = self.conn.execute(
                "SELECT * FROM v_active_routing_patterns ORDER BY priority DESC, pattern_name"
            ).fetchall()
            rules = [dict(row) for row in rows]
        except sqlite3.OperationalError:
            rules = [dict(row) if hasattr(row, 'keys') else row for row in self._get_builtin_patterns()]
        self._routing_rules_cache = rules
        return rules

    def _invalidate_routing_cache(self) -> None:
        self._routing_rules_cache = None
        self._routing_buckets_cache = None
        self._routing_fallback_cache = None
        self._route_lookup_cache = None

    def _load_route_lookup_cache(self) -> Dict[str, Dict[str, Any]]:
        if self._route_lookup_cache is not None:
            return self._route_lookup_cache
        lookup: Dict[str, Dict[str, Any]] = {}
        try:
            cur = self.conn.cursor()
            for row in cur.execute("SELECT route_name, input_pattern, command_template, scope, enabled FROM control_command_routes WHERE enabled = 1"):
                lookup[row[0]] = {
                    "route_name": row[0],
                    "route_type": "control_command",
                    "input_pattern": row[1],
                    "command_template": row[2],
                    "description": row[3],
                    "enabled": row[4],
                }
            for row in cur.execute("SELECT route_name, input_pattern, handler, required_capability, output_contract, enabled FROM agent_tool_routes WHERE enabled = 1"):
                lookup[row[0]] = {
                    "route_name": row[0],
                    "route_type": "agent_tool",
                    "input_pattern": row[1],
                    "handler": row[2],
                    "required_capability": row[3],
                    "output_contract": row[4],
                    "enabled": row[5],
                }
        except sqlite3.OperationalError:
            lookup = {}
        self._route_lookup_cache = lookup
        return lookup

    def _pattern_prefixes(self, pattern_spec: str) -> List[str]:
        """Delegate routing-prefix extraction to the matching module."""
        return pattern_prefixes(pattern_spec)

    def _literal_prefix(self, text: str) -> Optional[str]:
        """Delegate literal-prefix extraction to the matching module."""
        return literal_prefix(text)

    def _build_routing_cache(self) -> None:
        """Build routing indexes using the matching module."""
        rules, buckets, fallback, route_lookup = build_routing_indexes(
            self.load_routing_rules(),
            self._load_route_lookup_cache(),
        )
        self._routing_rules_cache = rules
        self._routing_buckets_cache = buckets
        self._routing_fallback_cache = fallback
        self._route_lookup_cache = route_lookup

    def _route_candidates_for_text(self, normalized_text: str) -> List[Dict[str, Any]]:
        if self._routing_buckets_cache is None or self._routing_fallback_cache is None:
            self._build_routing_cache()
        assert self._routing_buckets_cache is not None
        assert self._routing_fallback_cache is not None
        return route_candidates_for_text(
            normalized_text,
            self._routing_buckets_cache,
            self._routing_fallback_cache,
        )

    def _match_routing_rule(self, pattern: Dict[str, Any], normalized_text: str, parsed_input: Optional[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
        """Match one routing rule using the matching module."""
        return match_routing_rule(pattern, normalized_text, parsed_input)

    def _route_mode_enabled(self) -> bool:
        cur = self.conn.cursor()
        row = cur.execute(
            "SELECT enabled FROM feature_flags WHERE feature_key='route_mode'"
        ).fetchone()
        return bool(row and row[0] == 1)

    def _match_route_mode_command(self, normalized_text: str) -> Optional[Dict[str, Any]]:
        match = re.match(r'^(?:mode\s+)?route(?:\s+mode)?\s+(on|off|status)$', normalized_text, re.IGNORECASE)
        if not match:
            return None
        action = match.group(1).lower()
        route_name_map = {
            'on': 'route_on',
            'off': 'route_off',
            'status': 'route_status',
        }
        route_name = route_name_map[action]
        cur = self.conn.cursor()
        route = cur.execute(
            "SELECT * FROM control_command_routes WHERE route_name = ? AND enabled = 1",
            (route_name,),
        ).fetchone()
        if route is None:
            return {
                "matched_pattern": f"route_mode_{action}",
                "route_name": route_name,
                "route_type": "control_command",
                "command_template": f"python3 mode_command.py route {action} --db continuity.db",
                "input_pattern": normalized_text,
                "parameters": {"input_text": normalized_text, "group1": action},
                "priority": 100,
                "description": "Toggle or inspect route-recognition mode.",
            }
        return {
            "matched_pattern": f"route_mode_{action}",
            "route_name": route_name,
            "route_type": "control_command",
            "command_template": route["command_template"],
            "input_pattern": route["input_pattern"],
            "parameters": {"input_text": normalized_text, "group1": action},
            "priority": 100,
            "description": route["scope"],
        }

    def _get_builtin_patterns(self) -> List[Dict[str, Any]]:
        """Get built-in routing patterns as fallback."""
        return [
            {
                "pattern_name": "create_decision",
                "pattern_type": "json_value",
                "pattern_spec": "create_decision",
                "route_name": "decide",
                "route_type": "control_command",
                "priority": 10,
                "description": "Matches inputs that explicitly create decisions"
            },
            {
                "pattern_name": "read_memory",
                "pattern_type": "json_path",
                "pattern_spec": "$.intent",
                "route_name": "memory_recall",
                "route_type": "control_command",
                "priority": 8,
                "description": "Matches memory recall requests"
            },
            {
                "pattern_name": "plan_workflow",
                "pattern_type": "json_regex",
                "pattern_spec": "^plan_",
                "route_name": "plan_start",
                "route_type": "control_command",
                "priority": 7,
                "description": "Matches plan workflow commands"
            },
            {
                "pattern_name": "tool_action",
                "pattern_type": "json_value",
                "pattern_spec": "execute",
                "route_name": "code_tool",
                "route_type": "agent_tool",
                "priority": 6,
                "description": "Matches tool execution requests"
            },
            {
                "pattern_name": "info_about",
                "pattern_type": "json_regex",
                "pattern_spec": "^info about (.+)$",
                "route_name": "info_about",
                "route_type": "control_command",
                "priority": 9,
                "description": "Matches 'info about <attributes>' requests"
            },
            {
                "pattern_name": "set_model",
                "pattern_type": "json_regex",
                "pattern_spec": "^(?:/model:set|set\\s+model)\\s+([^\\s]+)$",
                "route_name": "session_model_set",
                "route_type": "control_command",
                "priority": 9,
                "description": "Matches '/model:set <model_id>' or 'set model <model_id>' requests"
            }
        ]

    def _parse_input(self, input_text: str, input_type: str) -> Tuple[Any, str]:
        """Delegate input parsing to the isolated parsing module."""
        return parse_input(input_text, input_type)

    def match_input_to_route(self, input_text: str, input_type: str = "text") -> Dict[str, Any]:
        """Match input against routing patterns and determine action.
        
        Args:
            input_text: The user input text
            input_type: Type of input ("text", "json", "structured")
            
        Returns:
            Dictionary with routing decision details
        """
        parsed_input, normalized_text = self._parse_input(input_text, input_type)

        route_mode_match = self._match_route_mode_command(normalized_text)
        if route_mode_match:
            return route_mode_match

        # input_action_router.py is itself an explicit routing entrypoint: if it is
        # invoked, route-shaped input must always be accepted.  The route_mode
        # feature flag is kept for status/toggle visibility, but it must not gate
        # this CLI/router path.
        if self._routing_rules_cache is None or self._routing_buckets_cache is None:
            self._build_routing_cache()

        patterns = self.load_routing_rules()
        candidate_patterns = patterns if parsed_input else self._route_candidates_for_text(normalized_text)
        route_lookup = self._load_route_lookup_cache()

        for pattern in candidate_patterns:
            matched, extracted = self._match_routing_rule(pattern, normalized_text, parsed_input)
            if not matched:
                continue

            route_name = pattern.get("route_name")
            route_type = pattern.get("route_type")
            route = route_lookup.get(route_name, {}) if isinstance(route_name, str) else {}
            decision = {
                "matched_pattern": pattern.get("pattern_name"),
                "route_name": route_name,
                "route_type": route_type,
                "command_template": route.get("command_template"),
                "handler": route.get("handler"),
                "required_capability": route.get("required_capability"),
                "output_contract": route.get("output_contract"),
                "input_pattern": route.get("input_pattern") or pattern.get("pattern_spec"),
                "parameters": extracted,
                "priority": pattern.get("priority", -1),
                "description": route.get("description") or pattern.get("description"),
            }
            if route_type == "agent_tool" and not decision.get("handler"):
                decision["handler"] = route.get("handler")
            return decision

        # No pattern matched: try memory recall as a DB key/content search fallback.
        recall_packet = self._recall_for_unmatched_input(normalized_text)
        if recall_packet.get("hit_count", 0) > 0:
            return {
                "matched_pattern": "memory_recall_fallback",
                "route_name": "memory_recall_fallback",
                "route_type": "memory_recall",
                "action_type": "recall",
                "parameters": {"input_text": normalized_text, "query": normalized_text},
                "priority": -1,
                "description": "No routing pattern matched; returning memory recall hits.",
                "recall_packet": recall_packet,
            }

        # No pattern or memory match - report that nothing was found.
        return {
            "matched_pattern": None,
            "route_name": None,
            "route_type": None,
            "action_type": "unknown",
            "parameters": {"input_text": normalized_text, "query": normalized_text},
            "priority": -1,
            "description": "No matching routing pattern or memory recall hit found",
            "recall_packet": recall_packet,
        }

    def _recall_for_unmatched_input(self, normalized_text: str, limit: int = 5) -> Dict[str, Any]:
        """Use the memory_command recall API when route matching has no immediate hit."""
        query = re.sub(r"^[/?#>:-]+", "", normalized_text or "").strip()
        query = re.sub(r"\s+", " ", query).strip(" ?!.,;:\t\n\r")
        if not query:
            return {"query": query, "hit_count": 0, "hits": [], "error": "empty query"}
        try:
            from memory_command import build_working_packet, format_table_context, retrieve_memory, retrieve_table_context

            table_packet = retrieve_table_context(query, db_path=self.db_path, limit=limit)
            if table_packet.get("hit_count", 0) > 0:
                table_packet["result"] = format_table_context(table_packet)
                return table_packet

            # Ask the recall API for a small preview, then keep only true key/content
            # matches. The generic recall scorer can return high-confidence recent
            # items even with no lexical overlap; route fallback should not treat
            # those as a found key.
            packet = retrieve_memory(query, db_path=self.db_path, limit=max(limit, 10))
            tokens = [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9_'-]+", query)]
            strict_hits = []
            for hit in packet.get("hits") or []:
                haystack = " ".join(
                    str(hit.get(key) or "")
                    for key in ("source_type", "source_key", "title", "body", "condition")
                ).lower()
                if tokens and any(token in haystack for token in tokens):
                    strict_hits.append(hit)
            packet["hits"] = strict_hits[:limit]
            packet["hit_count"] = len(packet["hits"])
            old_working_packet = packet.get("working_packet") or {}
            packet["working_packet"] = build_working_packet(
                packet.get("query") or query,
                packet["hits"],
                focus=old_working_packet.get("focus"),
                policy=old_working_packet.get("policy") or [],
            )
            return packet
        except Exception as exc:
            return {"query": query, "hit_count": 0, "hits": [], "error": str(exc)}

    def _preview_text(self, value: Any, limit: int = 1000) -> Optional[str]:
        """Return a bounded, single-field text summary for DB stats/receipts."""
        if value is None:
            return None
        if isinstance(value, str):
            text = value
        else:
            try:
                text = json.dumps(value, ensure_ascii=False, sort_keys=True)
            except TypeError:
                text = str(value)
        text = text.strip()
        if len(text) > limit:
            return text[:limit] + "..."
        return text or None

    def _action_warning(self, action_result: Any) -> Optional[str]:
        if isinstance(action_result, dict):
            warning = action_result.get("warning") or action_result.get("warnings")
            return self._preview_text(warning, limit=500)
        return None

    def _action_error(self, action_result: Any) -> Optional[str]:
        if isinstance(action_result, dict):
            error = action_result.get("error") or action_result.get("error_message")
            return self._preview_text(error, limit=500)
        return None

    def _summarize_action_result(self, action_result: Any) -> Optional[str]:
        if isinstance(action_result, dict):
            for key in ("status", "message", "warning", "error", "value", "result", "assistant_text"):
                value = action_result.get(key)
                if value:
                    return self._preview_text({key: value}, limit=2000)
        return self._preview_text(action_result, limit=2000)

    def _importance_reason(self, decision: Dict[str, Any], success: bool, action_result: Any, error_message: Optional[str]) -> Optional[str]:
        """Decide whether this execution deserves a detailed receipt.

        Routine successful read-only routes are represented only in route_usage_stats.
        Detailed rows are kept for failures, warnings, state-changing route families,
        or receipt/audit route families.
        """
        route_name = str(decision.get("route_name") or "unknown")
        if not success or error_message or self._action_error(action_result):
            return "error"
        if self._action_warning(action_result):
            return "warning"
        if route_name.startswith(("plan_", "receipt_", "promotion_", "hypothesis_", "evidence_")):
            return "state_or_audit_route"
        if route_name.startswith("memory_") and not route_name.startswith("memory_recall"):
            return "state_or_audit_route"
        if route_name in {"report_gap", "route_on", "route_off", "session_model_set"}:
            return "state_changing_route"
        return None

    def _record_route_usage(self, decision: Dict[str, Any], input_text: str, timestamp: str,
                            success: bool, action_result: Any, error_message: Optional[str]) -> None:
        route_name = str(decision.get("route_name") or "unmatched")
        route_type = str(decision.get("route_type") or "unknown")
        warning = self._action_warning(action_result)
        error = error_message or self._action_error(action_result)
        result_preview = self._summarize_action_result(action_result)
        input_preview = self._preview_text(input_text, limit=500)
        self.conn.execute("""
            INSERT INTO route_usage_stats (
                route_name, route_type, total_count, success_count, error_count, warning_count,
                first_used_at, last_used_at, last_success_at, last_error_at, last_warning_at,
                last_input_preview, last_result_preview, last_error
            ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(route_name, route_type) DO UPDATE SET
                total_count = total_count + 1,
                success_count = success_count + excluded.success_count,
                error_count = error_count + excluded.error_count,
                warning_count = warning_count + excluded.warning_count,
                last_used_at = excluded.last_used_at,
                last_success_at = COALESCE(excluded.last_success_at, route_usage_stats.last_success_at),
                last_error_at = COALESCE(excluded.last_error_at, route_usage_stats.last_error_at),
                last_warning_at = COALESCE(excluded.last_warning_at, route_usage_stats.last_warning_at),
                last_input_preview = excluded.last_input_preview,
                last_result_preview = excluded.last_result_preview,
                last_error = COALESCE(excluded.last_error, route_usage_stats.last_error)
        """, (
            route_name,
            route_type,
            1 if success else 0,
            0 if success else 1,
            1 if warning else 0,
            timestamp,
            timestamp,
            timestamp if success else None,
            timestamp if not success or error else None,
            timestamp if warning else None,
            input_preview,
            result_preview,
            error,
        ))

    def _record_route_receipt(self, decision: Dict[str, Any], input_text: str, timestamp: str,
                              success: bool, action_result: Any, error_message: Optional[str],
                              importance_reason: str, input_action_log_id: Optional[int] = None) -> None:
        self.conn.execute("""
            INSERT INTO route_execution_receipts (
                timestamp, route_name, route_type, input_text, success, importance_reason,
                result_summary, error_message, warning_message, decision_json, action_result_json,
                input_action_log_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            decision.get("route_name"),
            decision.get("route_type"),
            str(input_text),
            1 if success else 0,
            importance_reason,
            self._summarize_action_result(action_result),
            error_message or self._action_error(action_result),
            self._action_warning(action_result),
            self._preview_text(decision, limit=5000),
            self._preview_text(action_result, limit=5000),
            input_action_log_id,
        ))

    def execute_routing_decision(self, decision: Dict[str, Any], input_text: str,
                               planning_episode_id: Optional[int] = None,
                               loop_iteration: int = 0,
                               pid: Optional[str] = None) -> Dict[str, Any]:
        """Execute the routing decision and record the action.
        
        Args:
            decision: The routing decision
            input_text: Original input text
            planning_episode_id: ID of planning episode if part of loop
            loop_iteration: Current iteration number
            
        Returns:
            Execution result
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        success = False
        error_message = None
        action_result = None

        # Pattern recognition notification
        pattern_name = decision.get("matched_pattern")
        if pattern_name and self.verbose:
            print(f"{U_ACTION}: pattern found: {pattern_name}")

        try:
            if decision["route_type"] == "control_command":
                if self.verbose:
                    print(f"{U_ACTION}: working on: {decision.get('route_name')}")
                action_result = self._execute_control_command(decision, pid=pid)
                success = action_result is not None
            elif decision["route_type"] == "agent_tool":
                if self.verbose:
                    print(f"{U_ACTION}: working on: {decision.get('route_name')}")
                action_result = self._execute_agent_tool(decision)
                success = action_result is not None
            elif decision["route_type"] == "memory_recall":
                if self.verbose:
                    print(f"{U_ACTION}: working on: {decision.get('route_name')}")
                action_result = self._execute_memory_recall(decision)
                success = action_result is not None and not action_result.get("error")
            else:
                recall_packet = decision.get("recall_packet") or {}
                if "recall_packet" in decision:
                    message = "No matching route or memory recall hit found"
                elif decision.get("description") == "Route recognition mode is off":
                    message = "Route recognition mode is off; run: route on"
                else:
                    message = "Unknown route type"
                action_result = {"status": "not_found", "message": message, "recall": recall_packet}
                error_message = action_result.get("message", message)
                success = False

            pi_agent_warning = self._pi_agent_route_warning(decision)
            if pi_agent_warning:
                if isinstance(action_result, dict):
                    action_result.setdefault("warning", pi_agent_warning)
                else:
                    action_result = {
                        "status": "warning",
                        "result": action_result,
                        "warning": pi_agent_warning,
                    }

            action_error = self._action_error(action_result)
            if action_error:
                error_message = error_message or action_error
                success = False
            
        finally:
            cur = self.conn.cursor()
            receipt_reason = self._importance_reason(decision, success, action_result, error_message)
            input_action_log_id = None

            # Always update compact route stats.
            self._record_route_usage(decision, input_text, timestamp, success, action_result, error_message)

            # Detailed per-execution rows are only for important events.
            if receipt_reason:
                cur.execute("""
                    INSERT INTO input_action_log 
                    (timestamp, input_text, input_type, matched_route_name, 
                     matched_route_type, action_type, parameters, success, 
                     error_message, planning_episode_id, loop_iteration)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    input_text,
                    "text" if isinstance(input_text, str) else "structured",
                    decision.get("route_name"),
                    decision.get("route_type"),
                    "execute" if success else "record_only",
                    json.dumps(decision.get("parameters", {})),
                    1 if success else 0,
                    error_message,
                    planning_episode_id,
                    loop_iteration
                ))
                input_action_log_id = cur.lastrowid
                self._record_route_receipt(
                    decision, input_text, timestamp, success, action_result,
                    error_message, receipt_reason, input_action_log_id=input_action_log_id,
                )
            self.conn.commit()
        
        return {
            "success": success,
            "action_result": action_result,
            "timestamp": timestamp,
            "route_decision": decision,
            "loop_iteration": loop_iteration,
            "recorded": True,
            "stats_recorded": True,
            "receipt_recorded": bool(receipt_reason),
            "receipt_reason": receipt_reason,
        }

    def _pi_agent_route_warning(self, decision: Dict[str, Any]) -> Optional[str]:
        """Warn when a Pi-agent-related route runs without an active bridge."""
        route_type = decision.get("route_type")
        route_name = decision.get("route_name")
        table_by_type = {
            "agent_tool": "agent_tool_routes",
            "control_command": "control_command_routes",
        }
        route_table = table_by_type.get(route_type)
        if not route_table or not isinstance(route_name, str) or not route_name:
            return None

        tagged = self.conn.execute(
            """SELECT 1 FROM object_epistemic_tags
               WHERE object_type='route'
                 AND object_key=?
                 AND tag_key='epistemic:pi_agent_related'
               LIMIT 1""",
            (f"{route_table}:{route_name}",),
        ).fetchone()
        if not tagged:
            return None
        pi_agent = self.conn.execute(
            "SELECT enabled FROM feature_flags WHERE feature_key='pi_agent' LIMIT 1"
        ).fetchone()
        if pi_agent and not pi_agent["enabled"]:
            return (
                "Warning: pi agent should be active for this route; "
                "run 'pi_agent on' first."
            )
        if self._select_bridge_pid() is not None:
            return None
        return (
            "Warning: pi agent should be active for this route; "
            "no active Pi session bridge was found in the current setting."
        )

    def _execute_memory_recall(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        packet = decision.get("recall_packet") or {}
        if not packet:
            packet = self._recall_for_unmatched_input(str((decision.get("parameters") or {}).get("query") or ""))
        try:
            from memory_command import format_memory_recall, format_table_context

            rendered = format_table_context(packet) if packet.get("tables") is not None else format_memory_recall(packet)
        except Exception:
            rendered = json.dumps(packet, indent=2)
        return {
            "status": "recalled" if packet.get("hit_count", 0) > 0 else "not_found",
            "query": packet.get("query"),
            "hit_count": packet.get("hit_count", 0),
            "result": rendered,
            "recall": packet,
            "error": packet.get("error"),
        }

    def _render_command_template(self, command_template: str, params: Dict[str, Any]) -> str:
        rendered = command_template
        if not isinstance(rendered, str) or not rendered:
            return ""
        for key, value in params.items():
            if isinstance(value, (str, int, float, bool)):
                rendered = rendered.replace(f"<{key}>", str(value))
        if "group1" in params and isinstance(params.get("group1"), (str, int, float, bool)):
            rendered = rendered.replace("<prompt>", str(params["group1"]))
        return rendered

    def _scientific_key(self, text: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:60]
        return slug or f"hypothesis_{int(time.time())}"

    def _evidence_provenance(self, source: str, input_text: str) -> tuple[str, str]:
        source_lower = source.lower()
        actors = []
        if "peter" in source_lower or "user" in source_lower:
            actors.append({"actor": "Peter", "role": "requester_or_observer"})
        if "gpt" in source_lower or "assistant" in source_lower:
            actors.append({"actor": "GPT", "role": "reasoner_or_implementer"})
        if "code" in source_lower or "compile" in source_lower or "diagnostic" in source_lower or "tool" in source_lower:
            actors.append({"actor": "tool/code", "role": "validator_or_artifact"})
        if not actors:
            actors.append({"actor": "unspecified", "role": "source"})
        actors.append({"actor": "input_action_router", "role": "recorder", "input": input_text[:500]})
        return "+".join(actor["actor"] for actor in actors if actor["actor"] != "input_action_router"), json.dumps(actors, ensure_ascii=False)

    def _execute_science_command(self, route_name: str, params: Dict[str, Any], input_text: str) -> Dict[str, Any]:
        cur = self.conn.cursor()
        if route_name == "hypothesis_add":
            claim = str(params.get("group1") or "").strip()
            prediction = str(params.get("group2") or "").strip()
            falsifier = str(params.get("group3") or "").strip()
            if not claim or not prediction or not falsifier:
                return {"status": "invalid", "error": "claim, prediction, and falsifier are required"}
            base_key = self._scientific_key(claim)
            key = base_key
            suffix = 2
            while cur.execute("SELECT 1 FROM hypotheses WHERE hypothesis_key=? LIMIT 1", (key,)).fetchone():
                key = f"{base_key}_{suffix}"
                suffix += 1
            cur.execute("""
                INSERT INTO hypotheses (hypothesis_key, claim, prediction, expected_evidence, falsifier, confidence, status)
                VALUES (?, ?, ?, ?, ?, 0.5, 'active')
            """, (key, claim, prediction, f"Evidence should check prediction: {prediction}", falsifier))
            self.conn.commit()
            return {
                "status": "hypothesis_created",
                "hypothesis_id": cur.lastrowid,
                "hypothesis_key": key,
                "result": f"Created hypothesis {cur.lastrowid}: {claim}\nPrediction: {prediction}\nFalsifier: {falsifier}",
            }

        if route_name == "hypothesis_list":
            rows = cur.execute("""
                SELECT id, hypothesis_key, claim, confidence, status, prediction, falsifier
                FROM hypotheses
                WHERE status IN ('active','supported','weakened')
                ORDER BY updated_at DESC
                LIMIT 10
            """).fetchall()
            if not rows:
                return {"status": "listed", "result": "No active hypotheses."}
            lines = ["Active hypotheses:"]
            for row in rows:
                lines.append(f"{row['id']}. [{row['status']}, conf={row['confidence']}] {row['claim']}\n   predicts: {row['prediction']}\n   falsifier: {row['falsifier']}")
            return {"status": "listed", "count": len(rows), "result": "\n".join(lines)}

        if route_name == "evidence_add":
            hypothesis_id = int(str(params.get("group1") or "0"))
            relation = str(params.get("group2") or "neutral").strip().lower()
            observation = str(params.get("group3") or "").strip()
            source = str(params.get("group4") or "user_observation").strip()
            hyp = cur.execute("SELECT id, claim FROM hypotheses WHERE id=? LIMIT 1", (hypothesis_id,)).fetchone()
            if not hyp:
                return {"status": "not_found", "error": f"No hypothesis id={hypothesis_id}"}
            source_actor, provenance_json = self._evidence_provenance(source, input_text)
            cur.execute("""
                INSERT INTO evidence_ledger (source_type, source_ref, source_actor, provenance_json, observation, reliability)
                VALUES ('observation', ?, ?, ?, ?, 0.7)
            """, (source, source_actor, provenance_json, observation))
            evidence_id = cur.lastrowid
            cur.execute("""
                INSERT INTO hypothesis_evidence (hypothesis_id, evidence_id, relation, rationale)
                VALUES (?, ?, ?, ?)
            """, (hypothesis_id, evidence_id, relation, f"Added via route: {input_text}"))
            if relation == "supports":
                cur.execute("UPDATE hypotheses SET status='supported', updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='active'", (hypothesis_id,))
            elif relation in {"weakens", "falsifies"}:
                new_status = "falsified" if relation == "falsifies" else "weakened"
                cur.execute("UPDATE hypotheses SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_status, hypothesis_id))
            self.conn.commit()
            return {
                "status": "evidence_recorded",
                "hypothesis_id": hypothesis_id,
                "evidence_id": evidence_id,
                "relation": relation,
                "result": f"Recorded evidence {evidence_id} that {relation} hypothesis {hypothesis_id}.",
            }

        if route_name == "hypothesis_test":
            hypothesis_id = int(str(params.get("group1") or "0"))
            hyp = cur.execute("SELECT * FROM hypotheses WHERE id=? LIMIT 1", (hypothesis_id,)).fetchone()
            if not hyp:
                return {"status": "not_found", "error": f"No hypothesis id={hypothesis_id}"}
            rows = cur.execute("""
                SELECT he.relation, e.id AS evidence_id, e.observation, e.source_ref, e.reliability, e.recorded_at
                FROM hypothesis_evidence he
                JOIN evidence_ledger e ON e.id = he.evidence_id
                WHERE he.hypothesis_id=?
                ORDER BY e.recorded_at DESC
                LIMIT 10
            """, (hypothesis_id,)).fetchall()
            lines = [
                f"Hypothesis {hyp['id']} [{hyp['status']}, conf={hyp['confidence']}]: {hyp['claim']}",
                f"Prediction: {hyp['prediction']}",
                f"Expected evidence: {hyp['expected_evidence']}",
                f"Falsifier: {hyp['falsifier']}",
                "Evidence:",
            ]
            if rows:
                for row in rows:
                    lines.append(f"- {row['relation']} evidence {row['evidence_id']} (rel={row['reliability']}, source={row['source_ref']}): {row['observation']}")
            else:
                lines.append("- none yet")
            return {"status": "tested", "hypothesis_id": hypothesis_id, "result": "\n".join(lines)}

        if route_name == "hypothesis_confidence_update":
            hypothesis_id = int(str(params.get("group1") or "0"))
            new_conf = float(str(params.get("group2") or "0.5"))
            reason = str(params.get("group3") or "").strip()
            if new_conf < 0 or new_conf > 1:
                return {"status": "invalid", "error": "confidence must be between 0 and 1"}
            hyp = cur.execute("SELECT confidence FROM hypotheses WHERE id=? LIMIT 1", (hypothesis_id,)).fetchone()
            if not hyp:
                return {"status": "not_found", "error": f"No hypothesis id={hypothesis_id}"}
            old_conf = float(hyp["confidence"])
            cur.execute("UPDATE hypotheses SET confidence=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_conf, hypothesis_id))
            cur.execute("""
                INSERT INTO belief_confidence_updates (target_type, target_id, confidence_before, confidence_after, reason)
                VALUES ('hypothesis', ?, ?, ?, ?)
            """, (hypothesis_id, old_conf, new_conf, reason))
            self.conn.commit()
            return {
                "status": "confidence_updated",
                "hypothesis_id": hypothesis_id,
                "confidence_before": old_conf,
                "confidence_after": new_conf,
                "result": f"Updated hypothesis {hypothesis_id} confidence {old_conf} -> {new_conf} because {reason}",
            }

        return {"status": "unsupported", "error": f"Unsupported science command: {route_name}"}

    def _normalize_promotion_kind(self, kind: Optional[str]) -> str:
        value = (kind or "memory_fragment").strip().lower()
        if value in {"fragment", "memory_fragment"}:
            return "memory_fragment"
        if value == "reasoning_episode":
            return "reasoning_episode"
        return value

    def _source_summary_for_promotion(self, source_type: str, source_id: int) -> Optional[str]:
        if source_type in {"receipt", "route_receipt"}:
            row = self.conn.execute(
                "SELECT id, route_name, importance_reason, input_text, result_summary, error_message, warning_message FROM route_execution_receipts WHERE id=? LIMIT 1",
                (source_id,),
            ).fetchone()
            if not row:
                return None
            details = [
                f"route={row['route_name']}",
                f"importance={row['importance_reason']}",
                f"input={row['input_text']}",
            ]
            if row["warning_message"]:
                details.append(f"warning={row['warning_message']}")
            if row["error_message"]:
                details.append(f"error={row['error_message']}")
            if row["result_summary"]:
                details.append(f"result={row['result_summary']}")
            return " | ".join(details)
        return None

    def _execute_promotion_command(self, route_name: str, params: Dict[str, Any], input_text: str) -> Dict[str, Any]:
        cur = self.conn.cursor()
        if route_name == "promotion_candidate_add":
            source_type = str(params.get("group1") or "route_receipt")
            source_id = int(str(params.get("group2") or "0"))
            candidate_kind = self._normalize_promotion_kind(str(params.get("group3") or "memory_fragment"))
            reason = str(params.get("group4") or "").strip()
            summary = self._source_summary_for_promotion(source_type, source_id)
            if not summary:
                return {"status": "not_found", "error": f"No promotable {source_type} with id={source_id}"}
            cur.execute("""
                INSERT INTO promotion_candidates (source_type, source_id, candidate_kind, reason, summary, score, status)
                VALUES (?, ?, ?, ?, ?, 0.7, 'pending')
                ON CONFLICT(source_type, source_id, candidate_kind) DO UPDATE SET
                    reason=excluded.reason,
                    summary=excluded.summary,
                    status='pending',
                    updated_at=CURRENT_TIMESTAMP
            """, (source_type, source_id, candidate_kind, reason, summary))
            self.conn.commit()
            candidate_id = cur.execute(
                "SELECT id FROM promotion_candidates WHERE source_type=? AND source_id=? AND candidate_kind=? LIMIT 1",
                (source_type, source_id, candidate_kind),
            ).fetchone()[0]
            return {"status": "candidate_created", "candidate_id": candidate_id, "candidate_kind": candidate_kind, "summary": summary}

        if route_name == "promotion_list":
            rows = cur.execute("""
                SELECT id, source_type, source_id, candidate_kind, reason, score, summary, created_at
                FROM promotion_candidates
                WHERE status='pending'
                ORDER BY score DESC, created_at DESC
                LIMIT 10
            """).fetchall()
            if not rows:
                return {"status": "listed", "result": "No pending promotion candidates."}
            lines = ["Pending promotion candidates:"]
            for row in rows:
                lines.append(f"{row['id']}. {row['candidate_kind']} from {row['source_type']}:{row['source_id']} score={row['score']} — {row['reason']}\n   {row['summary'][:240]}")
            return {"status": "listed", "count": len(rows), "result": "\n".join(lines)}

        if route_name == "promotion_reject":
            candidate_id = int(str(params.get("group1") or "0"))
            reason = str(params.get("group2") or "rejected by command").strip()
            cur.execute("""
                UPDATE promotion_candidates
                SET status='rejected', reason=reason || ' | rejection: ' || ?, updated_at=CURRENT_TIMESTAMP
                WHERE id=? AND status='pending'
            """, (reason, candidate_id))
            self.conn.commit()
            if cur.rowcount == 0:
                return {"status": "not_found", "error": f"No pending promotion candidate id={candidate_id}"}
            return {"status": "rejected", "candidate_id": candidate_id, "result": f"Rejected promotion candidate {candidate_id}."}

        if route_name == "promotion_apply":
            candidate_id = int(str(params.get("group1") or "0"))
            override_kind = self._normalize_promotion_kind(params.get("group2")) if params.get("group2") else None
            row = cur.execute("SELECT * FROM promotion_candidates WHERE id=? AND status='pending' LIMIT 1", (candidate_id,)).fetchone()
            if not row:
                return {"status": "not_found", "error": f"No pending promotion candidate id={candidate_id}"}
            kind = override_kind or row["candidate_kind"]
            now_key = int(time.time())
            if kind == "memory_fragment":
                fragment_key = f"promotion:{candidate_id}:fragment"
                content = f"Promoted candidate {candidate_id}: {row['summary']}\nReason: {row['reason']}"
                cur.execute("""
                    INSERT INTO memory_fragments (fragment_key, fragment_type, content, factual_status, confidence, salience, provenance_key, source_reference)
                    VALUES (?, 'promotion', ?, 'derived', ?, ?, ?, ?)
                    ON CONFLICT(fragment_key) DO UPDATE SET
                        content=excluded.content,
                        updated_at=CURRENT_TIMESTAMP
                """, (fragment_key, content, min(float(row["score"]), 0.95), min(float(row["score"]), 0.95), "promotion_candidate", f"{row['source_type']}:{row['source_id']}"))
                promoted_id = str(cur.execute("SELECT id FROM memory_fragments WHERE fragment_key=?", (fragment_key,)).fetchone()[0])
            elif kind == "reasoning_episode":
                episode_key = f"promotion:{candidate_id}:reasoning:{now_key}"
                cur.execute("""
                    INSERT INTO reasoning_episodes (episode_key, title, claim, evidence_summary, inference, uncertainty, confidence, next_action, status, source_mode)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', 'derived')
                """, (
                    episode_key,
                    f"Promotion candidate {candidate_id}",
                    row["reason"],
                    row["summary"],
                    "Candidate was promoted because it appears useful as durable reasoning context.",
                    "Promotion was command-driven; review if confidence or scope changes.",
                    min(float(row["score"]), 0.95),
                    "Use this episode as provenance for future memory consolidation.",
                ))
                promoted_id = str(cur.lastrowid)
            else:
                return {"status": "unsupported", "error": f"Unsupported promotion kind: {kind}"}
            cur.execute("""
                UPDATE promotion_candidates
                SET status='promoted', promoted_to_type=?, promoted_to_id=?, promoted_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (kind, promoted_id, candidate_id))
            self.conn.commit()
            return {"status": "promoted", "candidate_id": candidate_id, "promoted_to_type": kind, "promoted_to_id": promoted_id, "result": f"Promoted candidate {candidate_id} to {kind}:{promoted_id}"}

        return {"status": "unsupported", "error": f"Unsupported promotion command: {route_name}"}

    def _execute_control_command(self, decision: Dict[str, Any], pid: Optional[str] = None) -> Any:
        command_template = decision.get("command_template", "")
        route_name = decision.get("route_name")
        params = decision.get("parameters", {})
        input_text = params.get("input_text", "")
        if route_name in {"pi_agent_on", "pi_agent_off", "pi_agent_status"}:
            if route_name != "pi_agent_status":
                enabled = 1 if route_name == "pi_agent_on" else 0
                self.conn.execute(
                    "UPDATE feature_flags SET enabled=?, updated_by='Peter', updated_at=CURRENT_TIMESTAMP WHERE feature_key='pi_agent'",
                    (enabled,),
                )
                self.conn.commit()
            state = self.conn.execute(
                "SELECT feature_key, enabled, switchable, scope, updated_by, updated_at FROM feature_flags WHERE feature_key='pi_agent' LIMIT 1"
            ).fetchone()
            return {
                "status": "executed_control",
                "command": command_template,
                "term": "pi agent",
                "enabled": bool(state["enabled"]) if state else False,
                "state": "on" if state and state["enabled"] else "off",
                "result": f"pi agent is {'on' if state and state['enabled'] else 'off'}",
            }
        if route_name and str(route_name).startswith(("hypothesis_", "evidence_")):
            return self._execute_science_command(str(route_name), params, input_text)
        if route_name and str(route_name).startswith("promotion_"):
            return self._execute_promotion_command(str(route_name), params, input_text)
        gap_text = None
        # Extract captured group from regex for gap
        if route_name == "report_gap":
            m = re.search(r'^gap\s+(.+)$', input_text, re.IGNORECASE)
            if m:
                gap_text = m.group(1)
        if route_name == "report_gap" and gap_text:
            # 1) Add gap to DB (reasoning episode + open question assumption note)
            cur = self.conn.cursor()
            assumption = ("Origin assumption: user-reported gap; possible causes include "
                         "retrieval overlap, schema drift, or missing links.")
            cur.execute(
                "INSERT INTO reasoning_episodes (episode_key, title, claim, evidence_summary, "
                "inference, uncertainty, next_action, status, source_mode, confidence) "
                "SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ? "
                "WHERE NOT EXISTS (SELECT 1 FROM reasoning_episodes WHERE episode_key = ?)",
                (f"gap:{gap_text}", f"Gap: {gap_text}", gap_text,
                 "User-reported via input routing.",
                 "Requires DB improvement cycle review.", assumption,
                 "Run db_improvement_control_flow step verification.", "active", "derived", 0.5,
                 f"gap:{gap_text}"))
            cur.execute("SELECT id FROM reasoning_episodes WHERE episode_key = ?", (f"gap:{gap_text}",))
            episode_row = cur.fetchone()
            episode_id = episode_row[0] if episode_row else None
            # 2) Note origin assumption in open question
            cur.execute(
                "INSERT OR IGNORE INTO open_questions (question, status, origin_reasoning_episode_id) "
                "VALUES (?, ?, ?)",
                (f"Gap reported: {gap_text} — origin assumption?", "open", episode_id))
            # 3) Trigger db_improvement_control_flow — mark verify step in_progress
            cur.execute(
                "SELECT id FROM work_plans WHERE plan_key = ?",
                ("db_improvement_control_flow",))
            plan_row = cur.fetchone()
            if plan_row:
                cur.execute(
                    "UPDATE work_plan_steps SET status = 'in_progress' "
                    "WHERE plan_id = ? AND step_key = 'verify_on_real_tasks' "
                    "AND status IN ('pending', 'blocked')",
                    (plan_row[0],))
            self.conn.commit()
            return {"status": "executed_control", "command": command_template,
                    "gap_recorded": gap_text, "assumption_note": assumption,
                    "improvement_plan_triggered": True}
        if route_name == "memory_recall":
            query = params.get("group1") or input_text
            if isinstance(query, str):
                query = re.sub(r'^(?:memory\s+recall|recall)\s+', '', query, flags=re.IGNORECASE).strip()
            if not query:
                return {
                    "status": "executed_control",
                    "command": command_template,
                    "error": "Recall query is required",
                }
            from memory_command import format_memory_recall, retrieve_memory
            packet = retrieve_memory(str(query), db_path=DB_PATH)
            return {
                "status": "executed_control",
                "command": self._render_command_template(command_template, {**params, "query": query}),
                "query": query,
                "packet": packet,
                "result": format_memory_recall(packet),
            }
        if route_name == "info_about":
            m = re.search(r'^info about (.+)$', input_text, re.IGNORECASE)
            attributes = m.group(1) if m else input_text
            # Dot-notation JSON path navigation (e.g., context.data.model.thinkingLevel)
            path = attributes
            # Strip leading 'context.' since the bridge state root is the context
            if path.startswith("context."):
                path = path[len("context."):]
            # Fetch bridge session state
            from pi_session import get_session_state
            try:
                state = get_session_state(pid=pid)
            except Exception as exc:
                return {
                    "status": "executed_control",
                    "command": f"info_about {attributes}",
                    "attributes": attributes,
                    "path": path,
                    "error": f"Bridge state fetch failed: {exc}",
                    "session_state_available": False,
                }
            # Navigate dot path from the full state JSON
            keys = [k for k in path.split(".") if k]
            value = state
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return {
                        "status": "executed_control",
                        "command": f"info_about {attributes}",
                        "attributes": attributes,
                        "path": path,
                        "error": f"Key '{k}' not found in state at path '{path}'",
                        "session_state_available": True,
                    }
            return {
                "status": "executed_control",
                "command": f"info_about {attributes}",
                "attributes": attributes,
                "path": path,
                "value": value,
                "session_state_available": True,
            }
        if route_name == "session_model_set":
            model_id = params.get("group1") or input_text
            if not isinstance(model_id, str) or not model_id.strip():
                return {
                    "status": "executed_control",
                    "command": command_template,
                    "error": "Model id is required",
                }
            from pi_session import set_model
            model_id = model_id.strip()
            if "/" not in model_id:
                return {
                    "status": "executed_control",
                    "command": command_template,
                    "model_id": model_id,
                    "error": "Use provider/model_id, for example openrouter/free",
                }
            provider, model_name = model_id.split("/", 1)
            if not provider or not model_name:
                return {
                    "status": "executed_control",
                    "command": command_template,
                    "model_id": model_id,
                    "error": "Use provider/model_id, for example openrouter/free",
                }
            session_result = set_model(provider, model_name, pid=pid)
            return {
                "status": "executed_control",
                "command": self._render_command_template(command_template, {**params, "group1": model_id}),
                "model_id": model_id,
                "provider": provider,
                "value": f"Switched model: {model_id}",
                "session_result": session_result,
            }
        if route_name == "session_latest_answer":
            raw_pid = params.get("group1") or params.get("pid") or pid
            session_pid = str(raw_pid).strip() if raw_pid is not None else None
            if session_pid in {"", "None", "null"}:
                session_pid = None
            from pi_session import latest_assistant_text
            assistant_text = latest_assistant_text(pid=session_pid)
            command = self._render_command_template(command_template, {**params, "pid": session_pid or ""})
            return {
                "status": "executed_control",
                "command": command,
                "pid": session_pid,
                "assistant_text": assistant_text,
            }
        if route_name == "session_chat_at":
            raw_index = params.get("group1") or "-1"
            try:
                index = int(str(raw_index).strip())
            except ValueError:
                index = -1
            raw_pid = params.get("group2") or params.get("pid") or pid
            session_pid = str(raw_pid).strip() if raw_pid is not None else None
            if session_pid in {"", "None", "null"}:
                session_pid = None
            from pi_session import get_session_history
            history = get_session_history(pid=session_pid, limit=100, event="message_end", max_bytes=10_000_000)
            events = ((history.get("data") or {}).get("events") or [])
            responses = []
            for event in events:
                msg = event.get("message") or (event.get("data") or {}).get("message") or {}
                if msg.get("role") != "assistant":
                    continue
                parts = []
                content = msg.get("content") or []
                if isinstance(content, str):
                    parts.append(content)
                elif isinstance(content, list):
                    for chunk in content:
                        if isinstance(chunk, dict) and chunk.get("type") == "text" and isinstance(chunk.get("text"), str):
                            parts.append(chunk["text"])
                text = "\n".join(parts).strip()
                if text:
                    responses.append({"timestamp": event.get("timestamp"), "text": text})
            if not responses:
                return {
                    "status": "executed_control",
                    "command": self._render_command_template(command_template, {**params, "pid": session_pid or "", "index": index}),
                    "pid": session_pid,
                    "index": index,
                    "error": "No assistant message_end responses found",
                }
            try:
                selected = responses[index] if index < 0 else responses[index - 1]
            except IndexError:
                return {
                    "status": "executed_control",
                    "command": self._render_command_template(command_template, {**params, "pid": session_pid or "", "index": index}),
                    "pid": session_pid,
                    "index": index,
                    "available_count": len(responses),
                    "error": f"Chat index out of range; available assistant responses: {len(responses)}",
                }
            return {
                "status": "executed_control",
                "command": self._render_command_template(command_template, {**params, "pid": session_pid or "", "index": index}),
                "pid": session_pid,
                "index": index,
                "timestamp": selected.get("timestamp"),
                "assistant_text": selected.get("text"),
            }
        if route_name == "session_chat_since":
            since = str(params.get("group1") or "").strip()
            raw_pid = params.get("group2") or params.get("pid") or pid
            session_pid = str(raw_pid).strip() if raw_pid is not None else None
            if session_pid in {"", "None", "null"}:
                session_pid = None
            if not since:
                return {
                    "status": "executed_control",
                    "command": command_template,
                    "error": "Timestamp is required, e.g. /chat since 2026-09-09T04:24:00Z",
                }
            from pi_session import get_session_history
            history = get_session_history(pid=session_pid, limit=500, since=since, event="message_end", max_bytes=20_000_000)
            events = ((history.get("data") or {}).get("events") or [])
            lines = []
            for event in events:
                msg = event.get("message") or (event.get("data") or {}).get("message") or {}
                role = msg.get("role")
                if role not in {"user", "assistant"}:
                    continue
                parts = []
                content = msg.get("content") or []
                if isinstance(content, str):
                    parts.append(content)
                elif isinstance(content, list):
                    for chunk in content:
                        if isinstance(chunk, dict) and chunk.get("type") == "text" and isinstance(chunk.get("text"), str):
                            parts.append(chunk["text"])
                text = "\n".join(parts).strip()
                if text:
                    lines.append(f"--- {role} @ {event.get('timestamp')} ---\n{text}")
            rendered = "\n\n".join(lines)
            return {
                "status": "executed_control",
                "command": self._render_command_template(command_template, {**params, "pid": session_pid or "", "since": since}),
                "pid": session_pid,
                "since": since,
                "count": len(lines),
                "assistant_text": rendered or "No user/assistant chat messages found since timestamp.",
            }
        if route_name == "session_prompt":
            prompt = params.get("group1") or params.get("input_text", "")
            from pi_session import prompt_session
            from shlex import quote
            session_result = prompt_session(prompt, pid=pid)
            return {
                "status": "executed_control",
                "command": command_template.replace("<prompt>", quote(prompt)),
                "prompt": prompt,
                "assistant_text": session_result.get("assistant_text"),
                "session_result": session_result,
            }
        if route_name in {"route_on", "route_off", "route_status"}:
            from mode_command import run_mode_command
            action = "status"
            if route_name.endswith("_on"):
                action = "on"
            elif route_name.endswith("_off"):
                action = "off"
            result = json.loads(run_mode_command(["route", action], db_path=self.db_path))
            return {
                "status": "executed_control",
                "command": command_template,
                "mode_result": result,
            }
        return {"status": "executed_control", "command": command_template}

    def _execute_agent_tool(self, decision: Dict[str, Any]) -> Any:
        handler = decision.get("handler")
        if handler == "context_info":
            return self._execute_context_info_tool(decision)
        if handler == "controlled_tag_assign":
            groups = (decision.get("parameters") or {}).get("groups") or []
            if len(groups) != 3:
                return {"status": "rejected", "reason": "controlled tag route requires object type, object key, and existing tag"}
            from helper_for_db import _controlled_tag_assign
            try:
                with sqlite3.connect(self.db_path) as con:
                    con.row_factory = sqlite3.Row
                    result = _controlled_tag_assign(con, groups[0], groups[1], groups[2])
            except ValueError as error:
                return {
                    "status": "rejected",
                    "code": getattr(error, "code", "tagging_not_possible"),
                    "message": str(error),
                    "details": getattr(error, "details", {}),
                }
            return result

        # Integration with agent_tool_routes
        return {"status": "executed_agent", "handler": handler}

    def _bridge_binary(self) -> Optional[Path]:
        candidates = [
            ROOT / ".pi/bin/pi-bridge",
            Path.home() / ".pi/agent/bin/pi-bridge",
            Path.home() / ".pi/agent/npm/node_modules/@vanillagreen/pi-session-bridge/bin/pi-bridge.js",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _bridge_command(self, *args: str, timeout: int = 20) -> Any:
        bridge = self._bridge_binary()
        if bridge is None:
            raise FileNotFoundError("pi-bridge CLI not found")

        if bridge.suffix == ".js":
            command = ["node", str(bridge), *args]
        else:
            command = [str(bridge), *args]

        output = subprocess.check_output(command, text=True, stderr=subprocess.STDOUT, timeout=timeout)
        return json.loads(output)

    def _select_bridge_pid(self) -> Optional[int]:
        try:
            instances = self._bridge_command("list", "--json")
        except Exception:
            return None

        if not isinstance(instances, list):
            return None

        workspace = str(ROOT)
        matches = [
            inst for inst in instances
            if inst.get("cwd") == workspace and inst.get("alive") and inst.get("socketExists")
        ]
        if not matches:
            matches = [
                inst for inst in instances
                if inst.get("alive") and inst.get("socketExists")
            ]
        if not matches:
            return None
        return int(matches[0]["pid"])

    def _bridge_request(self, pid: int, payload: Dict[str, Any], timeout: int = 20) -> Any:
        request = dict(payload)
        request.setdefault("id", f"iar-{int(time.time() * 1000)}")
        return self._bridge_command("request", "--pid", str(pid), json.dumps(request), timeout=timeout)

    def _extract_tool_text(self, history_response: Dict[str, Any], tool_name: str) -> Optional[str]:
        events = ((history_response or {}).get("data") or {}).get("events") or []
        for event in reversed(events):
            data = event.get("data") or {}
            if event.get("event") != "tool_execution_end":
                continue
            if data.get("toolName") != tool_name:
                continue
            result = data.get("result") or {}
            for chunk in result.get("content") or []:
                if isinstance(chunk, dict) and chunk.get("type") == "text" and chunk.get("text"):
                    return chunk["text"]
        return None

    def _execute_context_info_tool(self, decision: Dict[str, Any]) -> Any:
        pid = self._select_bridge_pid()
        if pid is None:
            return {
                "status": "executed_agent",
                "handler": "context_info",
                "available": False,
                "error": "No active pi-session-bridge target found",
            }

        try:
            commands_response = self._bridge_request(pid, {"type": "get_commands"})
            commands = (((commands_response or {}).get("data") or {}).get("commands") or [])
            command_names = {cmd.get("name") for cmd in commands if isinstance(cmd, dict)}
            has_context_info = "context_info" in command_names

            # Try the direct slash route first when the command is present.
            send_response = self._bridge_request(pid, {"type": "send", "message": "/context_info"})

            result_text = None
            for _ in range(5):
                history_response = self._bridge_request(
                    pid,
                    {"type": "history", "limit": 20, "event": "tool_execution_end"},
                )
                result_text = self._extract_tool_text(history_response, "context_info")
                if result_text:
                    break
                time.sleep(0.25)

            if result_text:
                return {
                    "status": "executed_agent",
                    "handler": "context_info",
                    "available": has_context_info,
                    "pid": pid,
                    "bridge": send_response,
                    "result": result_text,
                }

            bridge_data = (send_response or {}).get("data") if isinstance(send_response, dict) else {}
            slash_error = bridge_data.get("slashDispatchError") if isinstance(bridge_data, dict) else None
            slash_fallback = bridge_data.get("slashDispatchFallback") if isinstance(bridge_data, dict) else None
            detail = "context_info tool result was not observed in bridge history"
            if slash_error or slash_fallback:
                detail += f"; slashDispatchFallback={slash_fallback}; slashDispatchError={slash_error}"
            return {
                "status": "unavailable",
                "handler": "context_info",
                "available": False,
                "pid": pid,
                "bridge": send_response,
                "warning": detail,
                "result": detail,
            }
        except Exception as exc:
            return {
                "status": "executed_agent",
                "handler": "context_info",
                "available": False,
                "pid": pid,
                "error": str(exc),
            }

    def _format_plain_result(self, result: Dict[str, Any]) -> List[str]:
        action_result = result.get("action_result") or {}
        lines: List[str] = []

        assistant_text = action_result.get("assistant_text") or action_result.get("reply_text")
        if isinstance(assistant_text, str) and assistant_text.strip():
            lines.append(assistant_text.strip())
            return lines

        session_text = self._extract_session_text(action_result.get("session_result"))
        if session_text:
            lines.append(session_text)
            return lines

        text = action_result.get("result")
        if isinstance(text, str) and text.strip():
            lines.append(text.strip())
            return lines

        # Show the queried value if present (e.g., info_about return value)
        value = action_result.get("value")
        if isinstance(value, (str, int, float, bool)) and value:
            lines.append(f"value: {value}")
            return lines

        if action_result.get("command"):
            lines.append(str(action_result["command"]))

        message = action_result.get("message")
        if isinstance(message, str) and message.strip():
            lines.append(message.strip())

        warning = action_result.get("warning")
        if isinstance(warning, str) and warning.strip():
            lines.append(warning.strip())

        error = action_result.get("error")
        if isinstance(error, str) and error.strip():
            lines.append(error.strip())

        if not lines:
            lines.append(json.dumps(action_result, indent=2))
        return lines

    def _extract_session_text(self, session_result: Any) -> Optional[str]:
        if not isinstance(session_result, dict):
            return None

        def pick_text(node: Any) -> Optional[str]:
            if isinstance(node, str):
                return node.strip() or None
            if isinstance(node, list):
                for item in node:
                    found = pick_text(item)
                    if found:
                        return found
                return None
            if isinstance(node, dict):
                for key in ("text", "message", "result", "content", "output"):
                    if key in node:
                        found = pick_text(node[key])
                        if found:
                            return found
                data = node.get("data")
                if isinstance(data, dict):
                    for key in ("text", "message", "result", "content", "output", "deliveredAs"):
                        value = data.get(key)
                        if isinstance(value, str) and value.strip():
                            return value.strip()
                        found = pick_text(value)
                        if found:
                            return found
                return None
            return None

        for key in ("assistant_text", "reply_text"):
            value = session_result.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        history = session_result.get("history")
        if isinstance(history, dict):
            events = ((history.get("data") or {}).get("events") or [])
            for event in reversed(events):
                data = event.get("data") or {}
                message = data.get("message") or data.get("partial")
                if not isinstance(message, dict) or message.get("role") != "assistant":
                    continue
                content = message.get("content") or []
                if isinstance(content, str) and content.strip():
                    return content.strip()
                if isinstance(content, list):
                    for chunk in reversed(content):
                        if isinstance(chunk, dict):
                            if chunk.get("type") == "text" and isinstance(chunk.get("text"), str) and chunk["text"].strip():
                                return chunk["text"].strip()
                            if isinstance(chunk.get("text"), str) and chunk["text"].strip():
                                return chunk["text"].strip()

        send = session_result.get("send")
        if isinstance(send, dict):
            found = pick_text(send)
            if found:
                return found

        state = session_result.get("state")
        if isinstance(state, dict):
            found = pick_text(state)
            if found:
                return found

        return pick_text(session_result)

    def process_continuous_input(self, source="stdin") -> Dict[str, Any]:
        """Process a single input continuously. Returns routing decision."""
        if source == "stdin":
            input_text = sys.stdin.read().strip()
        else:
            input_text = ""
            
        if not input_text:
            return {"status": "empty_input", "action": None}
        
        # Try JSON parsing
        input_type = "text"
        try:
            parsed = json.loads(input_text)
            input_type = "json"
        except:
            pass
        
        decision = self.match_input_to_route(input_text, input_type)
        result = self.execute_routing_decision(decision, input_text, pid=self.pid)
        return result

    def start_loop(self, loop_key: str = "default") -> None:
        """Start continuous loop planning mode (in-memory state)."""
        self.loop_mode = True
        self.running = True
        self.current_plan = loop_key
        # Re-seed patterns from current routes (in case routes were added)
        self.seed_patterns_from_routes()
        self.conn.commit()

        print(f"[Router] Continuous loop started: {loop_key}")
        iteration = 0

        while self.running and self.loop_mode:
            try:
                print(f"\n[Loop {loop_key} / iteration {iteration}] Waiting for input (or 'exit' to stop):")
                line = input().strip()
                if line.lower() == "exit":
                    break
                if not line:
                    continue
                decision = self.match_input_to_route(line, "text")
                result = self.execute_routing_decision(decision, line, pid=self.pid)
                if self.running and self.loop_mode:
                    for output_line in self._format_plain_result(result):
                        print(output_line)
                iteration += 1
            except EOFError:
                break
            except Exception as e:
                print(f"[Router] Loop error: {e}")

    def stop(self):
        self.running = False
        self.loop_mode = False
        try:
            self.conn.close()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Continuous input action router")
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--pid", default=None, help="pi-session-bridge PID for session tools")
    parser.add_argument("--continuous", "--contin", action="store_true", help="Run continuously")
    parser.add_argument("--loop", action="store_true", help="Run in loop planning mode")
    parser.add_argument("--single", type=str, default=None, help="Process single input text")
    parser.add_argument("--plan-key", type=str, default="default")
    parser.add_argument("--format", type=str, default="plain", choices=["plain","json"])
    parser.add_argument("--watch", nargs=3, action="append", metavar=("TEXT", "ROUTE", "ROUTEARG"), help="Add watch rule and start polling loop. TEXT is matched against latest chat message; ROUTE is the route to trigger; ROUTEARG is the route argument. Can repeat.")
    parser.add_argument("--sleep", type=int, default=30, help="Poll interval in seconds for --watch (default: 30)")
    args = parser.parse_args()
    
    router = InputActionRouter(Path(args.db), pid=args.pid)

    if args.watch:
        from watch_route import add_watch, start_watch
        for watch_entry in args.watch:
            text, route, routearg = watch_entry
            add_watch(router.conn, text, route, routearg)
            print(f"added watch: text='{text}' route={route} arg={routearg}")
        start_watch(router.conn, args.sleep, pid=args.pid, router=router)
        return

    if args.single:
        result = router.match_input_to_route(args.single, "text")
        result = router.execute_routing_decision(result, args.single, pid=args.pid)
        if args.format == "plain":
            for output_line in router._format_plain_result(result):
                print(output_line)
            return
        print(json.dumps(result, indent=2))
    elif args.loop:
        router.start_loop(args.plan_key)
    elif args.continuous:
        router.running = True
        while router.running:
            try:
                line = input("iar> ").strip()
            except EOFError:
                break
            if not line:
                continue
            if line.lower() in ("exit", "quit"):
                break
            decision = router.match_input_to_route(line, "text")
            result = router.execute_routing_decision(decision, line, pid=args.pid)
            if args.format == "plain":
                for output_line in router._format_plain_result(result):
                    print(output_line)
                continue
            print(json.dumps(result, indent=2))
    else:
        print("Usage: input_action_router --single <text>")
        print("       input_action_router --continuous")
        print("       input_action_router --loop --plan-key <key>")


if __name__ == "__main__":
    main()
