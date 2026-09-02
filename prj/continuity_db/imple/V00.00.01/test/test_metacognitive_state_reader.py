from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import unittest
from io import StringIO
from contextlib import redirect_stdout
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from metacognitive_state_reader import fetch_metacognitive_state, summarize_metacognitive_state, main


class MetacognitiveStateReaderTests(unittest.TestCase):
    def test_fetch_metacognitive_state_reads_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_copy = Path(tmp) / "continuity.db"
            shutil.copy2(REPO_ROOT / "continuity.db", db_copy)
            conn = sqlite3.connect(db_copy)
            try:
                rows = fetch_metacognitive_state(conn)
            finally:
                conn.close()
            self.assertGreaterEqual(len(rows), 3)
            keys = {row["state_key"] for row in rows}
            self.assertIn("primary_goal", keys)
            self.assertIn("current_focus", keys)

    def test_summarize_metacognitive_state_includes_goal_and_focus(self):
        rows = [
            {
                "state_key": "primary_goal",
                "category": "goals",
                "value": "Learn how to think well",
                "confidence": 0.98,
                "provenance": "peter",
                "version": 3,
                "updated_at": "2026-01-01T00:00:00Z",
            },
            {
                "state_key": "current_focus",
                "category": "attention",
                "value": "Develop coherent reasoning",
                "confidence": 0.95,
                "provenance": "current",
                "version": 1,
                "updated_at": "2026-01-01T00:00:00Z",
            },
        ]
        text = summarize_metacognitive_state(rows)
        self.assertIn("primary_goal", text)
        self.assertIn("current_focus", text)
        self.assertIn("Learn how to think well", text)
        self.assertIn("Develop coherent reasoning", text)

    def test_main_prints_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_copy = Path(tmp) / "continuity.db"
            shutil.copy2(REPO_ROOT / "continuity.db", db_copy)
            buf = StringIO()
            with redirect_stdout(buf):
                exit_code = main(["--db", str(db_copy), "--json"])
            self.assertEqual(exit_code, 0)
            payload = json.loads(buf.getvalue())
            self.assertIn("rows", payload)
            self.assertIn("summary", payload)
            self.assertGreaterEqual(payload["count"], 3)


if __name__ == "__main__":
    unittest.main()
