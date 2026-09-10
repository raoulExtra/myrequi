import json, shutil, sqlite3, tempfile, unittest, argparse
from pathlib import Path
import helper_for_db


class TDD_CodeReceiptTests(unittest.TestCase):
    def test_epistemic_receipt_created_for_approved_passed_run(self):
        """After an approved+passed code run, an epistemic_receipt exists."""
        tmpdir = Path(tempfile.mkdtemp())
        db = tmpdir / "continuity.db"
        shutil.copy2(helper_for_db.DEFAULT_DB, db)

        # Create an approved+passed artifact
        conn = sqlite3.connect(db)
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO code_artifacts(name, description) VALUES (?, ?)", ("ep_receipt_art", "receipt test"))
            aid = cur.lastrowid
            cur.execute(
                "INSERT INTO code_versions(artifact_id, version, source, sha256, validation_status, validation_notes, approval_status) VALUES (?,?,?,?,?,?,?)",
                (aid, 1, "source", "hash_ep", "passed", "[]", "approved"),
            )
            conn.commit()
        finally:
            conn.close()

        # Count existing receipts for code_version before run
        conn = sqlite3.connect(db)
        before = conn.execute("SELECT count(*) FROM epistemic_receipts WHERE object_type='code_version'").fetchone()[0]
        conn.close()

        # Run the artifact (will fail because no actual code, but receipt logic runs first)
        import sys
        try:
            helper_for_db.cmd_run(argparse.Namespace(name="ep_receipt_art", db=db, timeout=1, program_args=[]))
        except SystemExit:
            pass  # expected; code execution fails but receipt creation ran

        # Verify receipt was created
        conn = sqlite3.connect(db)
        try:
            receipt = conn.execute(
                "SELECT COUNT(*) FROM epistemic_receipts WHERE object_type='code_version' AND object_version='1'"
            ).fetchone()[0]
            self.assertGreater(receipt, before, "an epistemic_receipt must be created for the code run")
            # Verify provenance content
            prov = json.loads(conn.execute(
                "SELECT provenance_json FROM epistemic_receipts WHERE object_type='code_version' LIMIT 1"
            ).fetchone()[0])
            self.assertEqual(prov["origin"], "cmd_run")
            self.assertIn("artifact", prov["detail"])
            self.assertEqual(prov["detail"]["validation_status"], "passed")
        finally:
            conn.close()
        shutil.rmtree(tmpdir)


if __name__ == "__main__":
    unittest.main()