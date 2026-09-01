from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from requi_file_checker_sim import explain_run, parse_cli


class RequiFileCheckerSimTests(unittest.TestCase):
    def test_parse_cli_resolves_paths(self):
        parsed = parse_cli([
            "--root", "prj/demo",
            "--json-in", "examples/r4_1_checker/config.json",
        ])
        self.assertEqual(parsed["marker"], "REF_EXISTS")
        self.assertTrue(str(parsed["requirement"]).endswith("004-requi-continuity-db-starter-guidance.md"))
        self.assertTrue(str(parsed["evidence"]).endswith("memory-and-filesystem-guidance.md"))

    def test_explain_run_returns_narrated_text(self):
        text = explain_run([
            "--root", "prj/demo",
            "--json-in", "examples/r4_1_checker/config.json",
        ])
        self.assertIn("1. set root to prj/demo", text)
        self.assertIn("load arg config from", text)
        self.assertIn("extract terms from the requirement using term[MARKER] lines", text)
        self.assertIn("would check link target 004.1-requi-continuity-db-file-level-evidence.md", text)
        self.assertIn("finish with a simulated result", text)


if __name__ == "__main__":
    unittest.main()
