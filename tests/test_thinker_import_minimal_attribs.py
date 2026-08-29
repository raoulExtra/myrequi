import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path('thinker/import_minimal_attribs.py')
DB_PATH = Path('thinker/thinker.db')


class ThinkerImportMinimalAttribsTests(unittest.TestCase):
    def test_relation_last_activated_is_indexed_into_attribs(self):
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
                    "select name from attribs where name='relations.last_activated'"
                ).fetchone()
            finally:
                conn.close()

            self.assertIsNotNone(row)
        finally:
            shutil.rmtree(tmpdir)


if __name__ == '__main__':
    unittest.main()
