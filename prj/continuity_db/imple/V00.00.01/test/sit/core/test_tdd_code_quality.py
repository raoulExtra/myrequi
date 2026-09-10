import json, shutil, sqlite3, tempfile, unittest, argparse
from pathlib import Path
import helper_for_db


class TDD_CodeQualityTests(unittest.TestCase):
    def _setup_artifact(self, db, name, ethics_tier="full"):
        conn = sqlite3.connect(db)
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO code_artifacts(name, description, ethics_tier) VALUES (?, ?, ?)",
                (name, f"test artifact for quality tier {ethics_tier}", ethics_tier),
            )
            aid = cur.lastrowid
            cur.execute(
                "INSERT INTO code_versions(artifact_id, version, source, sha256, validation_status, validation_notes, approval_status) VALUES (?,?,?,?,?,?,?)",
                (aid, 1, "source", "hash_qc", "passed", "[]", "approved"),
            )
            conn.commit()
        finally:
            conn.close()

    def test_quality_checks_added_to_continuity_check_items(self):
        """Quality checks are recorded in continuity_check_items."""
        tmpdir = Path(tempfile.mkdtemp())
        db = tmpdir / "continuity.db"
        shutil.copy2(helper_for_db.DEFAULT_DB, db)
        self._setup_artifact(db, "qc_test_art", ethics_tier="full")

        # Run the artifact to trigger quality check insertion
        try:
            helper_for_db.cmd_run(argparse.Namespace(name="qc_test_art", db=db, timeout=1, program_args=[]))
        except SystemExit:
            pass  # expected

        # Query for quality-related check keys
        conn = sqlite3.connect(db)
        try:
            qc_checks = [
                "lint",
                "formatting",
                "complexity",
                "security",
                "testing",
                "documentation",
                "performance",
                "code_style",
            ]
            found = []
            for ck in qc_checks:
                row = conn.execute(
                    "SELECT check_key FROM continuity_check_items WHERE check_key = ?", (ck,)
                ).fetchone()
                if row:
                    found.append(ck)
            self.assertTrue(len(found) > 0, f"No quality checks found in continuity_check_items. Found: {found}")
        finally:
            conn.close()
        shutil.rmtree(tmpdir)

    def test_quality_checks_with_minimal_tier(self):
        """Minimal ethics tier still allows quality checks to be recorded."""
        tmpdir = Path(tempfile.mkdtemp())
        db = tmpdir / "continuity.db"
        shutil.copy2(helper_for_db.DEFAULT_DB, db)
        self._setup_artifact(db, "qc_minimal_art", ethics_tier="minimal")

        # Run the artifact to trigger quality check insertion
        try:
            helper_for_db.cmd_run(argparse.Namespace(name="qc_minimal_art", db=db, timeout=1, program_args=[]))
        except SystemExit:
            pass  # expected

        # Quality checks should still be recorded
        conn = sqlite3.connect(db)
        try:
            qc_checks = ["lint", "formatting", "complexity"]
            for ck in qc_checks:
                row = conn.execute(
                    "SELECT check_key FROM continuity_check_items WHERE check_key = ?", (ck,)
                ).fetchone()
                self.assertIsNotNone(row, f"Quality check {ck} not found in continuity_check_items after minimal tier run")
        finally:
            conn.close()
        shutil.rmtree(tmpdir)


if __name__ == "__main__":
    unittest.main()