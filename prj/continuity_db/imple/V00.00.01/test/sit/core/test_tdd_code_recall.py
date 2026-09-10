import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

import memory_command


class TDD_CodeRecallTests(unittest.TestCase):
    def test_code_artifact_recall_in_memory_index(self):
        tmpdir = Path(tempfile.mkdtemp())
        db = tmpdir / "continuity.db"
        shutil.copy2(memory_command.DB_PATH, db)

        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO code_artifacts(name, description) VALUES (?, ?)",
            ("tdd_code_token_art", "tdd recall token"),
        )
        artifact_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO code_versions
            (artifact_id, version, source, sha256, validation_status, validation_notes, approval_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (artifact_id, 1, "source", "hash", "passed", "[]", "approved"),
        )
        conn.commit()
        conn.close()

        result = json.loads(memory_command.run_memory_recall("tdd recall token", db_path=db))
        self.assertEqual(result["query"], "tdd recall token")
        self.assertGreaterEqual(result["hit_count"], 1)
        self.assertIn("code_artifact", {hit["source_type"] for hit in result["hits"]})
        self.assertIn("tdd_code_token_art", json.dumps(result))
        shutil.rmtree(tmpdir)

    def test_approved_code_ranks_above_pending(self):
        """validation_status + approval_status become confidence signals."""
        tmpdir = Path(tempfile.mkdtemp())
        db = tmpdir / "continuity.db"
        shutil.copy2(memory_command.DB_PATH, db)

        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO code_artifacts(name, description) VALUES (?, ?)",
            ("approved_artifact", "validation approval token"),
        )
        approved_id = cur.lastrowid
        cur.execute(
            "INSERT INTO code_versions(artifact_id, version, source, sha256, validation_status, validation_notes, approval_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (approved_id, 1, "source", "hash1", "passed", "[]", "approved"),
        )
        cur.execute(
            "INSERT INTO code_artifacts(name, description) VALUES (?, ?)",
            ("pending_artifact", "validation approval token"),
        )
        pending_id = cur.lastrowid
        cur.execute(
            "INSERT INTO code_versions(artifact_id, version, source, sha256, validation_status, validation_notes, approval_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (pending_id, 1, "source", "hash2", "passed", "[]", "pending"),
        )
        conn.commit()
        conn.close()

        result = json.loads(memory_command.run_memory_recall("validation approval token", db_path=db, limit=10))
        sources = [(h["source_type"], h.get("confidence"), h["title"]) for h in result["hits"]]
        approved_hit = next((s for s in sources if s[2] == "approved_artifact"), None)
        pending_hit = next((s for s in sources if s[2] == "pending_artifact"), None)
        self.assertIsNotNone(approved_hit, "approved artifact must appear in recall")
        self.assertIsNotNone(pending_hit, "pending artifact must appear in recall")
        self.assertGreater(
            approved_hit[1], pending_hit[1],
            "approved artifact confidence must exceed pending",
        )
        shutil.rmtree(tmpdir)


if __name__ == "__main__":
    unittest.main()
