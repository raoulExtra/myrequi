import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[7] / "continuity.db"


def test_semantic_read_model_exposes_canonical_roles():
    with sqlite3.connect(DB_PATH) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(v_semantic_records)")]
        assert columns == [
            "semantic_type",
            "semantic_key",
            "statement",
            "confidence",
            "status",
            "source_table",
        ]
        roles = {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT semantic_type FROM v_semantic_records LIMIT 10"
            )
        }
        assert {"belief", "conviction", "metacognitive_state", "identity", "decision", "concept"} <= roles


def test_semantic_ownership_contract_covers_each_core_type():
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT semantic_type, canonical_role, prohibited_role, contract_version "
            "FROM semantic_ownership_contract LIMIT 10"
        ).fetchall()
        assert {row[0] for row in rows} == {
            "belief", "conviction", "metacognitive_state", "identity", "decision", "concept"
        }
        assert all(row[3] == 1 and row[1] and row[2] for row in rows)


def test_overlap_report_is_non_destructive_and_queryable():
    with sqlite3.connect(DB_PATH) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(v_semantic_overlap_candidates)")]
        assert columns == [
            "semantic_type", "semantic_key", "statement", "confidence",
            "status", "source_table", "normalized_statement",
        ]
        connection.execute("SELECT * FROM v_semantic_overlap_candidates LIMIT 10").fetchall()


def test_source_tables_have_fixed_semantic_types():
    with sqlite3.connect(DB_PATH) as connection:
        mismatches = connection.execute(
            """SELECT semantic_type, source_table FROM v_semantic_records
               WHERE (source_table='beliefs' AND semantic_type<>'belief')
                  OR (source_table='convictions' AND semantic_type<>'conviction')
                  OR (source_table='metacognitive_state' AND semantic_type<>'metacognitive_state')
                  OR (source_table='identity' AND semantic_type<>'identity')
                  OR (source_table='decisions' AND semantic_type<>'decision')
                  OR (source_table='concepts' AND semantic_type<>'concept')
               LIMIT 10"""
        ).fetchall()
        assert mismatches == []


def test_overlap_candidates_are_classified_without_source_deletion():
    with sqlite3.connect(DB_PATH) as connection:
        total = connection.execute(
            "SELECT COUNT(*) FROM v_semantic_overlap_candidates"
        ).fetchone()[0]
        classified = connection.execute(
            "SELECT COUNT(*) FROM semantic_overlap_classifications "
            "WHERE review_status='classified'"
        ).fetchone()[0]
        assert total >= classified * 2
        assert classified > 0
        assert connection.execute("SELECT COUNT(*) FROM beliefs").fetchone()[0] > 0
        assert connection.execute("SELECT COUNT(*) FROM convictions").fetchone()[0] > 0


def test_core_model_declares_distinct_semantic_ownership():
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT layer_key, purpose, current_tables, collapsed_concepts FROM v_core_model ORDER BY sort_order"
        ).fetchall()
        text = " ".join(" ".join(row) for row in rows)
        for name in ("beliefs", "convictions", "metacognitive_state", "identity", "decisions", "concepts"):
            assert name in text
        assert "canonical semantic ownership" in text.lower()
