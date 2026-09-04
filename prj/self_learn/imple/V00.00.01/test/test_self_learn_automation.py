from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import self_learn_automation as sla


class SelfLearnAutomationTests(unittest.TestCase):
    def test_sync_creates_dirs_and_moves_completed_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "plans").mkdir(parents=True)
            (root / "docs").mkdir(parents=True)
            (root / "plans" / "1_plan.md").write_text("status: completed\n", encoding="utf-8")
            (root / "plans" / "2_plan.md").write_text("status: active\n", encoding="utf-8")

            report = sla.sync(root)

            self.assertIn("plans/done/1_plan.md", report.moved_plans)
            self.assertTrue((root / "plans" / "done" / "1_plan.md").exists())
            self.assertTrue((root / "plans" / "2_plan.md").exists())
            self.assertTrue((root / "assets").exists())
            self.assertTrue((root / "imple" / "V00.00.01" / "test").exists())

    def test_refresh_writes_docs_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "plans" / "done").mkdir(parents=True)
            (root / "docs").mkdir(parents=True)
            (root / "docs" / "learning-loop.md").write_text("# loop\n", encoding="utf-8")
            (root / "plans" / "2_plan.md").write_text("status: active\n", encoding="utf-8")
            (root / "plans" / "1_plan.md").write_text("status: completed\n", encoding="utf-8")

            report = sla.refresh(root)

            self.assertTrue((root / "docs" / "index.md").exists())
            index = (root / "docs" / "index.md").read_text(encoding="utf-8")
            self.assertIn("learning-loop.md", index)
            self.assertIn("2_plan.md", index)
            self.assertIn("1_plan.md", index)
            self.assertIn("docs_index", report)

    def test_main_checkpoint_creates_git_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            project = repo / "prj" / "self_learn"
            (project / "plans" / "done").mkdir(parents=True)
            (project / "docs").mkdir(parents=True)
            (project / "plans" / "2_plan.md").write_text("status: completed\n", encoding="utf-8")
            (project / "docs" / "learning-loop.md").write_text("# loop\n", encoding="utf-8")
            (repo / "continuity.db").write_text("seed\n", encoding="utf-8")
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Self Learn"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "self_learn@example.com"], cwd=repo, check=True)

            rc = sla.main(["checkpoint", "--root", str(project)])

            self.assertEqual(rc, 0)
            log = subprocess.run(["git", "log", "--oneline", "-1"], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
            self.assertIn("self_learn: filesystem checkpoint", log)
            self.assertTrue((project / "plans" / "done" / "2_plan.md").exists())
            self.assertTrue((project / "docs" / "index.md").exists())

    def test_main_refresh_creates_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "plans" / "done").mkdir(parents=True)
            (root / "docs").mkdir(parents=True)
            (root / "plans" / "2_plan.md").write_text("status: active\n", encoding="utf-8")
            (root / "docs" / "learning-loop.md").write_text("# loop\n", encoding="utf-8")

            rc = sla.main(["refresh", "--root", str(root)])

            self.assertEqual(rc, 0)
            self.assertTrue((root / "docs" / "index.md").exists())
            index = (root / "docs" / "index.md").read_text(encoding="utf-8")
            self.assertIn("2_plan.md", index)
            self.assertIn("learning-loop.md", index)

    def test_status_reports_plans_and_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "plans" / "done").mkdir(parents=True)
            (root / "docs").mkdir(parents=True)
            (root / "plans" / "done" / "1_plan.md").write_text("status: completed\n", encoding="utf-8")
            (root / "plans" / "2_plan.md").write_text("status: active\n", encoding="utf-8")
            (root / "docs" / "learning-loop.md").write_text("# loop\n", encoding="utf-8")

            report = sla.status(root)

            self.assertEqual(report["active_plans"], ["2_plan.md"])
            self.assertEqual(report["done_plans"], ["1_plan.md"])
            self.assertIn("learning-loop.md", report["docs"])


if __name__ == "__main__":
    unittest.main()
