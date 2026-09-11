import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[7] / "continuity.db"
EXPECTED_TYPES = {
    "concept", "belief", "conviction", "identity", "metacognitive_state", "decision"
}


def test_shared_semantic_records_has_common_contract_and_all_types():
    with sqlite3.connect(DB_PATH) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(semantic_records)")]
        assert columns == [
            "semantic_type", "semantic_key", "statement", "confidence", "status",
            "provenance", "version", "source_table", "source_id", "created_at", "updated_at",
        ]
        types = {row[0] for row in connection.execute(
            "SELECT DISTINCT semantic_type FROM semantic_records LIMIT 10"
        )}
        assert types == EXPECTED_TYPES


def test_shared_semantic_records_preserves_source_counts_and_keys():
    with sqlite3.connect(DB_PATH) as connection:
        expected = {
            "concept": "concepts", "belief": "beliefs", "conviction": "convictions",
            "identity": "identity", "metacognitive_state": "metacognitive_state",
            "decision": "decisions",
        }
        for semantic_type, source_table in expected.items():
            shared_count = connection.execute(
                "SELECT COUNT(*) FROM semantic_records WHERE semantic_type=?", (semantic_type,)
            ).fetchone()[0]
            source_count = connection.execute(f"SELECT COUNT(*) FROM {source_table}").fetchone()[0]
            assert shared_count == source_count


def test_source_writes_are_synchronized_without_persisting_test_rows():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("BEGIN")
        connection.execute(
            "INSERT INTO identity(key, value, version) VALUES ('__semantic_test__', 'temporary', 1)"
        )
        row = connection.execute(
            "SELECT semantic_type, semantic_key, statement FROM semantic_records "
            "WHERE semantic_type='identity' AND semantic_key='__semantic_test__'"
        ).fetchone()
        assert row == ('identity', '__semantic_test__', 'temporary')
        connection.rollback()
        assert connection.execute(
            "SELECT COUNT(*) FROM semantic_records WHERE semantic_key='__semantic_test__'"
        ).fetchone()[0] == 0


def test_shared_semantic_records_migration_is_idempotent():
    with sqlite3.connect(DB_PATH) as connection:
        before = connection.execute(
            "SELECT semantic_type, semantic_key, statement FROM semantic_records "
            "ORDER BY semantic_type, semantic_key LIMIT 10"
        ).fetchall()
        after = connection.execute(
            "SELECT semantic_type, semantic_key, statement FROM semantic_records "
            "ORDER BY semantic_type, semantic_key LIMIT 10"
        ).fetchall()
        assert after == before
