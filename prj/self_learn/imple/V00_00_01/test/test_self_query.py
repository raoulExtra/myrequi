#!/usr/bin/env python3
"""Tests for self_query.py module."""

import json
import os
import sqlite3
import tempfile
from pathlib import Path
from unittest import TestCase, main

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from self_query import (
    get_db_connection,
    query_metacognitive_state,
    query_active_plans,
    query_open_questions,
    run_self_query,
)


class TestSelfQuery(TestCase):
    """Tests for self_query module."""

    def setUp(self):
        """Create a temporary test database and disable JSON file for these tests."""
        # Patch JSON path to non-existent temp file
        import self_query
        self.original_json_path = self_query.METACOGNITIVE_STATE_FILE
        self_query.METACOGNITIVE_STATE_FILE = Path(tempfile.mktemp(suffix=".json"))
        
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = Path(self.temp_db.name)
        self.temp_db.close()
        
        self.conn = sqlite3.connect(self.db_path)
        self._setup_schema()
        self._seed_data()

    def tearDown(self):
        """Clean up temporary database and restore JSON path."""
        import self_query
        self.conn.close()
        os.unlink(self.db_path)
        if self.original_json_path is not None:
            self_query.METACOGNITIVE_STATE_FILE = self.original_json_path

    def _setup_schema(self):
        """Create minimal schema for testing matching production DB."""
        cur = self.conn.cursor()
        
        cur.execute("""
            CREATE TABLE metacognitive_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state_key TEXT NOT NULL,
                category TEXT,
                value TEXT,
                confidence REAL,
                provenance TEXT,
                version INTEGER,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            CREATE TABLE work_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_key TEXT NOT NULL,
                title TEXT,
                objective TEXT,
                status TEXT DEFAULT 'active',
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                prompt TEXT DEFAULT ''
            )
        """)
        
        cur.execute("""
            CREATE TABLE work_plan_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER,
                step_order INTEGER,
                step_key TEXT,
                description TEXT,
                status TEXT DEFAULT 'pending',
                evidence TEXT,
                FOREIGN KEY (plan_id) REFERENCES work_plans(id)
            )
        """)
        
        cur.execute("""
            CREATE TABLE open_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                question TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                origin_reasoning_episode_id INTEGER,
                resolution_reasoning_episode_id INTEGER,
                resolution_note TEXT DEFAULT ''
            )
        """)
        
        cur.execute("""
            CREATE TABLE reasoning_episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                episode_key TEXT NOT NULL,
                title TEXT,
                claim TEXT,
                evidence_summary TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()

    def _seed_data(self):
        """Insert test data."""
        cur = self.conn.cursor()
        
        cur.execute("""
            INSERT INTO metacognitive_state (state_key, category, value, confidence, provenance, version)
            VALUES ('primary_goal', 'goals', 'Test primary goal', 0.95, 'test', 1)
        """)
        
        cur.execute("""
            INSERT INTO metacognitive_state (state_key, category, value, confidence, provenance, version)
            VALUES ('current_focus', 'focus', 'Test focus', 0.9, 'test', 1)
        """)
        
        cur.execute("""
            INSERT INTO work_plans (plan_key, title, objective, status, prompt)
            VALUES ('test_plan', 'Test Plan', 'Test objective', 'active', 'Test prompt')
        """)
        
        cur.execute("""
            INSERT INTO work_plan_steps (plan_id, step_order, step_key, description, status)
            VALUES (1, 1, 'step1', 'First step', 'pending')
        """)
        
        cur.execute("""
            INSERT INTO open_questions (question, status)
            VALUES ('Test question?', 'open')
        """)
        
        cur.execute("""
            INSERT INTO reasoning_episodes (episode_key, title, claim, evidence_summary)
            VALUES ('test_episode', 'Test Episode', 'Test claim', 'Test evidence')
        """)
        
        self.conn.commit()

    def test_get_db_connection(self):
        """Test database connection."""
        conn = get_db_connection(self.db_path)
        self.assertIsNotNone(conn)
        conn.close()

    def test_query_metacognitive_state_all(self):
        """Test querying all metacognitive state."""
        results = query_metacognitive_state(self.conn)
        self.assertEqual(len(results), 2)
        keys = [r["state_key"] for r in results]
        self.assertIn("current_focus", keys)
        self.assertIn("primary_goal", keys)

    def test_query_metacognitive_state_by_key(self):
        """Test querying specific metacognitive state."""
        results = query_metacognitive_state(self.conn, "primary_goal")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["state_key"], "primary_goal")
        self.assertEqual(results[0]["value"], "Test primary goal")

    def test_query_active_plans(self):
        """Test querying active plans."""
        plans = query_active_plans(self.conn)
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0]["plan_key"], "test_plan")
        self.assertEqual(len(plans[0]["steps"]), 1)

    def test_query_open_questions(self):
        """Test querying open questions."""
        questions = query_open_questions(self.conn)
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]["question"], "Test question?")

    def test_run_self_query_status(self):
        """Test status query."""
        result = run_self_query("status", self.db_path)
        self.assertEqual(result["type"], "status")
        self.assertEqual(len(result["primary_goal"]), 1)
        self.assertEqual(len(result["current_focus"]), 1)
        self.assertEqual(len(result["active_plans"]), 1)
        self.assertEqual(len(result["open_questions"]), 1)

    def test_run_self_query_goal(self):
        """Test goal query."""
        result = run_self_query("goal", self.db_path)
        self.assertEqual(result["type"], "goal")
        self.assertEqual(result["primary_goal"][0]["value"], "Test primary goal")

    def test_run_self_query_plans(self):
        """Test plans query."""
        result = run_self_query("plans", self.db_path)
        self.assertEqual(result["type"], "plans")
        self.assertEqual(len(result["active_plans"]), 1)

    def test_run_self_query_recall(self):
        """Test general recall query."""
        result = run_self_query("anything", self.db_path)
        self.assertEqual(result["type"], "recall")
        self.assertEqual(result["query"], "anything")


# Tests for R4: Filesystem-based metacognitive state

class TestJSONMetacognitiveState(TestCase):
    """Tests for JSON-based metacognitive state (R4)."""
    
    def setUp(self):
        """Set up test fixtures."""
        import tempfile
        self.temp_dir = Path(tempfile.mkdtemp())
        self.json_file = self.temp_dir / "metacognitive_state.json"
        
        import self_query
        self.original_json_path = self_query.METACOGNITIVE_STATE_FILE
        
    def tearDown(self):
        """Clean up test files."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        import self_query
        if self.original_json_path is not None:
            self_query.METACOGNITIVE_STATE_FILE = self.original_json_path
    
    def test_json_file_schema(self):
        """Test correct JSON schema for metacognitive_state."""
        test_data = {
            "migrated_from": "test_migration",
            "project": "self_learn",
            "entries": {
                "primary_goal": {
                    "value": "Test goal",
                    "category": "goals",
                    "confidence": 0.95,
                    "provenance": "test",
                    "version": 1
                }
            }
        }
        
        with open(self.json_file, "w") as f:
            json.dump(test_data, f)
        
        import self_query
        self_query.METACOGNITIVE_STATE_FILE = self.json_file
        
        from self_query import load_metacognitive_state_from_json
        state = load_metacognitive_state_from_json()
        self.assertIn("primary_goal", state)
        self.assertEqual(state["primary_goal"]["value"], "Test goal")
    
    def test_json_fallback_when_missing(self):
        """Test returns empty dict when JSON file doesn't exist."""
        import self_query
        self_query.METACOGNITIVE_STATE_FILE = self.json_file
        
        from self_query import load_metacognitive_state_from_json
        state = load_metacognitive_state_from_json()
        self.assertEqual(state, {})
    
    def test_query_json_priority(self):
        """Test that JSON values are returned when available."""
        test_data = {
            "entries": {
                "primary_goal": {
                    "value": "JSON goal value",
                    "category": "goals",
                    "confidence": 0.9,
                    "updated_at": "2026-09-06T00:00:00"
                }
            }
        }
        
        with open(self.json_file, "w") as f:
            json.dump(test_data, f)
        
        import self_query
        self_query.METACOGNITIVE_STATE_FILE = self.json_file
        
        # Create test DB
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE metacognitive_state (
                state_key TEXT PRIMARY KEY,
                value TEXT,
                category TEXT,
                confidence REAL,
                provenance TEXT,
                version INTEGER,
                updated_at TEXT
            )
        """)
        cur.execute("""
            INSERT INTO metacognitive_state VALUES 
            ('primary_goal', 'DB goal', 'goals', 0.8, 'db', 1, '2026-01-01')
        """)
        conn.commit()
        
        from self_query import query_metacognitive_state
        results = query_metacognitive_state(conn, "primary_goal")
        self.assertEqual(results[0]["value"], "JSON goal value")
        conn.close()


if __name__ == "__main__":
    main()