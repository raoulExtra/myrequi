import json, shutil, sqlite3, tempfile, unittest
from pathlib import Path
import memory_command


class TDD_CodeRunEpisodeTests(unittest.TestCase):
    def _get_ep_count_for_key(self, db, pattern):
        """Return count of episodes whose episode_key matches pattern."""
        conn = sqlite3.connect(db)
        try:
            return conn.execute(
                "SELECT count(*) FROM reasoning_episodes WHERE episode_key LIKE ?", (pattern,)
            ).fetchone()[0]
        finally:
            conn.close()

    def test_code_run_creates_reasoning_episode_when_approved_and_passed(self):
        """When a code artifact is approved+passed, cmd_run creates a reasoning_episode."""
        tmpdir = Path(tempfile.mkdtemp())
        db = tmpdir / "continuity.db"
        shutil.copy2(memory_command.DB_PATH, db)

        conn = sqlite3.connect(db)
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO code_artifacts(name, description) VALUES (?, ?)", ("tdd_episode_art", "episode test"))
            aid = cur.lastrowid
            cur.execute(
                "INSERT INTO code_versions(artifact_id, version, source, sha256, validation_status, validation_notes, approval_status) VALUES (?,?,?,?,?,?,?)",
                (aid, 1, "source", "hash", "passed", "[]", "approved"),
            )
            conn.commit()
        finally:
            conn.close()

        # Before run, no episode for this artifact
        before = self._get_ep_count_for_key(db, "code_run:tdd_episode_art:%")
        self.assertEqual(before, 0)

        # Run the artifact via helper_for_db cmd_run (using temp db)
        import helper_for_db as h
        h.cmd_run(h.parser().parse_args([
            "--db", str(db), "run", "tdd_episode_art", "--timeout", "1",
        ]))

        # After run, episode should exist
        after = self._get_ep_count_for_key(db, "code_run:tdd_episode_art:%")
        self.assertGreater(after, before, "episode must be created for approved+passed run")
        shutil.rmtree(tmpdir)

    def test_code_run_no_episode_when_not_approved(self):
        """Non-approved runs do NOT create an episode."""
        tmpdir = Path(tempfile.mkdtemp())
        db = tmpdir / "continuity.db"
        shutil.copy2(memory_command.DB_PATH, db)

        conn = sqlite3.connect(db)
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO code_artifacts(name, description) VALUES (?, ?)", ("tdd_no_ep_art", "no episode test"))
            aid = cur.lastrowid
            cur.execute(
                "INSERT INTO code_versions(artifact_id, version, source, sha256, validation_status, validation_notes, approval_status) VALUES (?,?,?,?,?,?,?)",
                (aid, 1, "source", "hash", "failed", "[]", "pending"),
            )
            conn.commit()
        finally:
            conn.close()

        before = self._get_ep_count_for_key(db, "code_run:tdd_no_ep_art:%")

        # Execution is denied for non-approved artifacts, so no episode should be created
        self.assertEqual(before, 0)

        # Try to run (should be denied)
        import helper_for_db as h
        try:
            h.cmd_run(h.parser().parse_args([
                "--db", str(db), "run", "tdd_no_ep_art", "--timeout", "1",
            ]))
        except SystemExit:
            pass  # expected

        after = self._get_ep_count_for_key(db, "code_run:tdd_no_ep_art:%")
        self.assertEqual(after, before, "no episode should be created for non-approved runs")
        shutil.rmtree(tmpdir)


if __name__ == "__main__":
    unittest.main()