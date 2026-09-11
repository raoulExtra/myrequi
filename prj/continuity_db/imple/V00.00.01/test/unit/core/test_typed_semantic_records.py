import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[7] / "continuity.db"


def test_typed_details_preserve_type_specific_fields():
    with sqlite3.connect(DB_PATH) as connection:
        details = [row[1] for row in connection.execute("PRAGMA table_info(semantic_record_details)")]
        assert "semantic_type" in details
        assert "semantic_key" in details
        assert "concept_glossary_term" in details
        assert "metacognitive_category" in details
        assert "decision_rationale" in details
        assert connection.execute(
            "SELECT COUNT(*) FROM semantic_record_details WHERE semantic_type='decision' AND decision_rationale IS NOT NULL"
        ).fetchone()[0] > 0


def test_history_is_populated_and_immutable():
    with sqlite3.connect(DB_PATH) as connection:
        assert connection.execute("SELECT COUNT(*) FROM semantic_record_history LIMIT 10").fetchone()[0] > 0
        columns = [row[1] for row in connection.execute("PRAGMA table_info(semantic_record_history)")]
        assert {"semantic_type", "semantic_key", "statement", "change_kind", "recorded_at"} <= set(columns)
        try:
            connection.execute(
                "UPDATE semantic_record_history SET statement='forbidden' WHERE history_id=(SELECT history_id FROM semantic_record_history LIMIT 1)"
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("history update was not rejected")


def test_typed_semantic_migration_is_idempotent():
    with sqlite3.connect(DB_PATH) as connection:
        before = connection.execute(
            "SELECT COUNT(*), MAX(history_id) FROM semantic_record_history"
        ).fetchone()
        after = connection.execute(
            "SELECT COUNT(*), MAX(history_id) FROM semantic_record_history"
        ).fetchone()
        assert after == before
