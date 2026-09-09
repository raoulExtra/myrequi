#!/usr/bin/env python3
"""
Query the cognition.db memory system for self-improvement purposes.

 ALSO reads from metacognitive_state.json for filesystem-based persistence.

Usage:
    python self_query.py "What do you remember about this project?"
    python self_query.py "status"
    python self_query.py "goal"
    python self_query.py "plans"
"""

import json
import sqlite3
from pathlib import Path

# Default database path - continuity.db at project root
# File is at: prj/self_learn/imple/V00_00_01/self_query.py
# Project root is 5 levels up: V00_00_01 -> imple -> self_learn -> prj -> myrequi
DEFAULT_DB = Path(__file__).resolve().parent.parent.parent.parent.parent / "continuity.db"

# Filesystem-based metacognitive state file
METACOGNITIVE_STATE_FILE = Path(__file__).resolve().parent.parent.parent / "metacognitive_state.json"


def load_metacognitive_state_from_json():
    """Load metacognitive state from filesystem JSON file."""
    if not METACOGNITIVE_STATE_FILE.exists():
        return {}
    try:
        with open(METACOGNITIVE_STATE_FILE) as f:
            data = json.load(f)
            return data.get("entries", {})
    except (json.JSONDecodeError, IOError):
        return {}


def get_db_connection(db_path=None):
    """Get a connection to the continuity.db database."""
    path = Path(db_path) if db_path else DEFAULT_DB
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def query_metacognitive_state(conn, state_key=None):
    """Query metacognitive state for goal, focus, or aspect. Checks JSON file first."""
    # First check filesystem-based JSON
    json_state = load_metacognitive_state_from_json()
    
    # Check if key exists in JSON file first
    if state_key and state_key in json_state:
        entry = json_state[state_key]
        return [{
            "state_key": state_key,
            "category": entry.get("category", "unknown"),
            "value": entry.get("value"),
            "confidence": entry.get("confidence"),
            "provenance": entry.get("provenance"),
            "version": entry.get("version"),
            "updated_at": entry.get("updated_at"),
        }]
    
    # Fall back to database
    cur = conn.cursor()
    if state_key:
        rows = cur.execute(
            "SELECT state_key, category, value, confidence, provenance, version, updated_at "
            "FROM metacognitive_state WHERE state_key=?",
            (state_key,),
        ).fetchall()
    else:
        rows = cur.execute(
            "SELECT state_key, category, value, confidence, provenance, version, updated_at "
            "FROM metacognitive_state "
            "WHERE state_key IN ('primary_goal', 'current_focus', 'current_aspect') "
            "ORDER BY state_key"
        ).fetchall()
    
    return [
        {
            "state_key": row[0],
            "category": row[1],
            "value": row[2],
            "confidence": row[3],
            "provenance": row[4],
            "version": row[5],
            "updated_at": row[6],
        }
        for row in rows
    ]


def query_active_plans(conn, limit=10):
    """Query active work plans with their steps."""
    cur = conn.cursor()
    plans = cur.execute(
        "SELECT id, plan_key, title, objective, status, created_at, updated_at, prompt "
        "FROM work_plans WHERE status='active' ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    result = []
    for plan in plans:
        # Get steps - use flexible column selection
        step_result = cur.execute(
            "SELECT step_order, step_key, description, status, evidence "
            "FROM work_plan_steps WHERE plan_id=? ORDER BY step_order",
            (plan[0],),
        ).fetchall()
        steps = []
        for step in step_result:
            step_dict = {
                "step_key": step[1],
                "description": step[2],
                "status": step[3],
                "evidence": step[4] if len(step) > 4 else None,
            }
            steps.append(step_dict)
        
        result.append({
            "plan_key": plan[1],
            "title": plan[2],
            "objective": plan[3],
            "status": plan[4],
            "prompt": plan[7] if len(plan) > 7 else None,
            "steps": steps,
        })
    return result


def query_open_questions(conn, limit=10):
    """Query open questions."""
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id, question, status, created_at, resolution_note "
        "FROM open_questions WHERE status IN ('open', 'deferred', 'partially_answered') "
        "ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [
        {
            "id": row[0],
            "question": row[1],
            "status": row[2],
            "created_at": row[3],
            "resolution_note": row[4] if len(row) > 4 else "",
        }
        for row in rows
    ]


def query_recent_episodes(conn, limit=10):
    """Query recent reasoning episodes."""
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT episode_key, title, claim, evidence_summary "
        "FROM reasoning_episodes ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [
        {
            "episode_key": row[0],
            "title": row[1],
            "claim": row[2],
            "evidence_summary": row[3],
        }
        for row in rows
    ]


def run_self_query(query, db_path=None):
    """Run a self-query and return structured results."""
    conn = get_db_connection(db_path)
    try:
        query_lower = query.lower().strip()
        
        if query_lower == "status":
            return {
                "type": "status",
                "primary_goal": query_metacognitive_state(conn, "primary_goal"),
                "current_focus": query_metacognitive_state(conn, "current_focus"),
                "current_aspect": query_metacognitive_state(conn, "current_aspect"),
                "active_plans": query_active_plans(conn),
                "open_questions": query_open_questions(conn),
            }
        
        elif query_lower == "goal":
            return {
                "type": "goal",
                "primary_goal": query_metacognitive_state(conn, "primary_goal"),
            }
        
        elif query_lower == "plans":
            return {
                "type": "plans",
                "active_plans": query_active_plans(conn),
            }
        
        else:
            # General recall query
            return {
                "type": "recall",
                "query": query,
                "primary_goal": query_metacognitive_state(conn, "primary_goal"),
                "current_focus": query_metacognitive_state(conn, "current_focus"),
                "active_plans": query_active_plans(conn, limit=5),
                "open_questions": query_open_questions(conn, limit=5),
                "recent_episodes": query_recent_episodes(conn, limit=5),
            }
    finally:
        conn.close()


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python self_query.py <query>")
        print("Examples: python self_query.py status")
        print("          python self_query.py goal")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    result = run_self_query(query)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()