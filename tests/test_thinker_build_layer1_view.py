import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path('thinker/build_layer1_view.py')
DB_PATH = Path('thinker/thinker.db')


class ThinkerBuildLayer1ViewTests(unittest.TestCase):
    def test_builds_layer1_materialized_view(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'thinker.db'
            shutil.copy2(DB_PATH, db_copy)

            subprocess.run(
                [sys.executable, str(SCRIPT_PATH), '--db', str(db_copy)],
                check=True,
                capture_output=True,
                text=True,
            )

            conn = sqlite3.connect(db_copy)
            try:
                row = conn.execute(
                    "select name, level, view_type, json_content from views where name='layer1_concept_index'"
                ).fetchone()
            finally:
                conn.close()

            self.assertIsNotNone(row)
            self.assertEqual(row[0], 'layer1_concept_index')
            self.assertEqual(row[1], 1)
            self.assertEqual(row[2], 'layer1_concept_index')
            self.assertIn('top_concepts', row[3])
            self.assertIn('json_paths', row[3])
        finally:
            shutil.rmtree(tmpdir)


if __name__ == '__main__':
    unittest.main()
