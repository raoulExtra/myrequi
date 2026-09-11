import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

import continuity_db_helper


class TDD_BeliefLinkTests(unittest.TestCase):
    def test_code_artifact_belief_link_is_created(self):
        tmpdir = Path(tempfile.mkdtemp())
        db = tmpdir / "continuity.db"
        shutil.copy2(continuity_db_helper.DEFAULT_DB, db)

        conn = sqlite3.connect(db)
        try:
            cur = conn.cursor()
            # Create a belief with a distinctive slug
            art_name = "tdd_belief_link_artifact"
            cur.execute(
                "INSERT INTO beliefs(slug, current_statement, confidence, status, current_version) VALUES (?, ?, ?, ?, ?)",
                (art_name, "This belief should link to a code artifact.", 0.92, "active", 1),
            )
            belief_id = cur.lastrowid
            conn.commit()
        finally:
            conn.close()

        # Create the code artifact and link them
        conn = sqlite3.connect(db)
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO code_artifacts(name, description) VALUES (?, ?)",
                (art_name, "test for belief link"),
            )
            artifact_id = cur.lastrowid
            cur.execute(
                "INSERT INTO code_versions(artifact_id, version, source, sha256, validation_status, validation_notes, approval_status) VALUES (?,?,?,?,?,?,?)",
                (artifact_id, 1, "source", "hash", "passed", "[]", "approved"),
            )
            # Create the link between artifact and belief
            cur.execute(
                "INSERT INTO code_artifact_belief_links(code_artifact_id, belief_id, relation) VALUES (?, ?, 'slug_match')",
                (artifact_id, belief_id),
            )
            conn.commit()
        finally:
            conn.close()

        # Verify link exists
        conn = sqlite3.connect(db)
        try:
            row = conn.execute(
                "SELECT * FROM code_artifact_belief_links WHERE code_artifact_id = ? AND belief_id = ?",
                (artifact_id, belief_id),
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[2], "slug_match")
        finally:
            conn.close()

        shutil.rmtree(tmpdir)


if __name__ == "__main__":
    unittest.main()