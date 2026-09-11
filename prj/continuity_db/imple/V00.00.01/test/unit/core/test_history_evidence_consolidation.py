import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[7] / "continuity.db"


def test_duplicate_history_is_consolidated_with_source_identity():
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT history_source_table, COUNT(*) FROM semantic_record_history WHERE history_source_table IS NOT NULL GROUP BY history_source_table LIMIT 10"
        ).fetchall()
        assert {row[0] for row in rows} >= {
            "belief_versions",
            "conviction_versions",
            "decision_versions",
            "metacognitive_state_history",
        }
        assert connection.execute(
            "SELECT COUNT(*) FROM semantic_record_history WHERE history_source_table='decision_versions' AND history_source_id IS NOT NULL"
        ).fetchone()[0] > 0


def test_evidence_tables_remain_distinct_and_populated():
    with sqlite3.connect(DB_PATH) as connection:
        for table in ("conviction_inputs", "concept_links", "reasoning_episodes"):
            assert connection.execute("SELECT COUNT(*) FROM " + table + " LIMIT 10").fetchone()[0] > 0


def test_history_source_identity_is_unique():
    with sqlite3.connect(DB_PATH) as connection:
        duplicate = connection.execute(
            "SELECT history_source_table,history_source_id,COUNT(*) FROM semantic_record_history WHERE history_source_table IS NOT NULL GROUP BY history_source_table,history_source_id HAVING COUNT(*) > 1 LIMIT 10"
        ).fetchall()
        assert duplicate == []
