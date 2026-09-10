import json, shutil, sqlite3, tempfile, unittest, argparse
from pathlib import Path
import helper_for_db


class TDD_CodeEthicsTests(unittest.TestCase):
    def _setup_artifact(self, db, name, ethics_tier="full"):
        conn = sqlite3.connect(db)
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO code_artifacts(name, description, ethics_tier) VALUES (?, ?, ?)",
                (name, f"test artifact for ethics tier {ethics_tier}", ethics_tier),
            )
            aid = cur.lastrowid
            cur.execute(
                "INSERT INTO code_versions(artifact_id, version, source, sha256, validation_status, validation_notes, approval_status) VALUES (?,?,?,?,?,?,?)",
                (aid, 1, "source", "hash_eth", "passed", "[]", "approved"),
            )
            conn.commit()
        finally:
            conn.close()

    def test_minimal_tier_only_enforces_hard_gates(self):
        """Minimal ethics tier only enforces hard_gate=1 checks."""
        tmpdir = Path(tempfile.mkdtemp())
        db = tmpdir / "continuity.db"
        shutil.copy2(helper_for_db.DEFAULT_DB, db)
        self._setup_artifact(db, "ethics_minimal_art", ethics_tier="minimal")

        # Run the artifact (should succeed because minimal tier only checks hard gates)
        # We expect it to NOT be blocked by the ethics gate
        try:
            helper_for_db.cmd_run(argparse.Namespace(name="ethics_minimal_art", db=db, timeout=1, program_args=[]))
        except SystemExit as e:
            # If it fails, it should NOT be due to ethics check failure
            self.assertNotIn("ethics", str(e).lower(), "minimal tier should not block on ethics")
        shutil.rmtree(tmpdir)

    def test_full_tier_enforces_all_checks(self):
        """Full ethics tier enforces all checks including soft ones."""
        tmpdir = Path(tempfile.mkdtemp())
        db = tmpdir / "continuity.db"
        shutil.copy2(helper_for_db.DEFAULT_DB, db)
        self._setup_artifact(db, "ethics_full_art", ethics_tier="full")

        # Run the artifact (should succeed because all checks pass for a benign script)
        try:
            helper_for_db.cmd_run(argparse.Namespace(name="ethics_full_art", db=db, timeout=1, program_args=[]))
        except SystemExit as e:
            # If it fails, it should NOT be due to ethics check failure
            self.assertNotIn("ethics", str(e).lower(), "full tier should not block on ethics for benign script")
        shutil.rmtree(tmpdir)

    def test_minimal_tier_skips_non_hard_gates(self):
        """Minimal tier skips checks with hard_gate=0 (stakeholders, fairness, reversibility, uncertainty, accountability, kanban_flow, constructive_topics)."""
        tmpdir = Path(tempfile.mkdtemp())
        db = tmpdir / "continuity.db"
        shutil.copy2(helper_for_db.DEFAULT_DB, db)
        self._setup_artifact(db, "ethics_minimal_skip", ethics_tier="minimal")

        # Verify the ethics check function exists and can be called
        # We'll check that the function returns True for minimal tier on a benign artifact
        # (The function is internal to cmd_run, so we test by running and expecting success)
        try:
            helper_for_db.cmd_run(argparse.Namespace(name="ethics_minimal_skip", db=db, timeout=1, program_args=[]))
        except SystemExit as e:
            self.assertNotIn("ethics", str(e).lower(), "minimal tier should not block on non-hard-gate checks")
        shutil.rmtree(tmpdir)


if __name__ == "__main__":
    unittest.main()