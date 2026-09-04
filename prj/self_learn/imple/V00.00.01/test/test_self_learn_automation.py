from __future__ import annotations

import json
import sqlite3
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
            (root / "phase_0.md").write_text("""PROJECT PHASE 0\npurpose: entry point\ngoal: keep navigation clear\noutcome: docs index stays useful\ncore_requirements:\n- define the canonical project entry point.\n- keep the glossary and automation links visible.\n- preserve the phase boundary into phase 1.\nstatus: completed\n""", encoding="utf-8")
            (root / "phase_1.md").write_text("""PROJECT PHASE 1\npurpose: choose a next path\ngoal: suggest the next path\noutcome: ranked path\ncore_requirements:\n- define the first usable path candidates.\n- challenge each candidate with explicit criteria.\n- keep a review loop and feedback path.\nstatus: active\n""", encoding="utf-8")

            report = sla.refresh(root)

            self.assertTrue((root / "docs" / "index.md").exists())
            self.assertTrue((root / "docs" / "glossary.md").exists())
            self.assertTrue((root / "docs" / "next-path.md").exists())
            self.assertTrue((root / "docs" / "phase-requirements.md").exists())
            self.assertTrue((root / "docs" / "phase-challenge.md").exists())
            self.assertTrue((root / "docs" / "modularity.md").exists())
            self.assertTrue((root / "docs" / "meta-trace.json").exists())
            self.assertTrue((root / "docs" / "meta-optimization.md").exists())
            index = (root / "docs" / "index.md").read_text(encoding="utf-8")
            self.assertIn("learning-loop.md", index)
            self.assertIn("glossary.md", index)
            self.assertIn("next-path.md", index)
            self.assertIn("phase-requirements.md", index)
            self.assertIn("phase-challenge.md", index)
            self.assertIn("modularity.md", index)
            self.assertIn("meta-optimization.md", index)
            self.assertIn("2_plan.md", index)
            self.assertIn("1_plan.md", index)
            self.assertIn("docs_index", report)
            self.assertIn("phase_requirements_report", report)
            self.assertIn("phase_manifest", report)
            self.assertIn("phase_challenge_bundle", report)
            self.assertEqual(report["modularity_budget"], [])

    def test_main_advance_creates_next_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            project = repo / "prj" / "self_learn"
            (project / "plans" / "done").mkdir(parents=True)
            (project / "docs").mkdir(parents=True)
            (project / "plans" / "3_plan.md").write_text("status: active\n", encoding="utf-8")
            (project / "plans" / "6_plan.md").write_text("status: active\n", encoding="utf-8")
            (project / "docs" / "learning-loop.md").write_text("# loop\n", encoding="utf-8")
            db = sqlite3.connect(repo / "continuity.db")
            db.execute("create table metacognitive_state(state_key text primary key, value text, version integer, updated_at text default current_timestamp)")
            db.execute("insert into metacognitive_state(state_key, value, version) values(?,?,?)", ('project_goal__self_learn', 'seed', 3))
            db.commit()
            db.close()
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Self Learn"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "self_learn@example.com"], cwd=repo, check=True)

            rc = sla.main(["advance", "--root", str(project)])

            self.assertEqual(rc, 0)
            log = subprocess.run(["git", "log", "--oneline", "-1"], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
            self.assertIn("self_learn: advance to phase 1", log)
            self.assertTrue((project / "phase_1.md").exists())
            self.assertTrue((project / "docs" / "glossary.md").exists())
            self.assertTrue((project / "docs" / "next-path.md").exists())
            self.assertTrue((project / "docs" / "phase-requirements.md").exists())
            self.assertTrue((project / "docs" / "phase-challenge.md").exists())
            self.assertTrue((project / "docs" / "modularity.md").exists())
            self.assertTrue((project / "docs" / "meta-trace.json").exists())
            self.assertTrue((project / "docs" / "meta-optimization.md").exists())
            self.assertTrue((project / "plans" / "done" / "3_plan.md").exists())
            self.assertTrue((project / "plans" / "done" / "6_plan.md").exists())
            self.assertTrue((project / "plans" / "7_plan.md").exists())
            self.assertTrue((project / "docs" / "index.md").exists())

    def test_main_checkpoint_creates_git_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            project = repo / "prj" / "self_learn"
            (project / "plans" / "done").mkdir(parents=True)
            (project / "docs").mkdir(parents=True)
            (project / "plans" / "3_plan.md").write_text("status: active\n", encoding="utf-8")
            (project / "plans" / "6_plan.md").write_text("status: active\n", encoding="utf-8")
            (project / "docs" / "learning-loop.md").write_text("# loop\n", encoding="utf-8")
            db = sqlite3.connect(repo / "continuity.db")
            db.execute("create table metacognitive_state(state_key text primary key, value text, version integer, updated_at text default current_timestamp)")
            db.execute("insert into metacognitive_state(state_key, value, version) values(?,?,?)", ('project_goal__self_learn', 'seed', 3))
            db.commit()
            db.close()
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Self Learn"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "self_learn@example.com"], cwd=repo, check=True)

            rc = sla.main(["checkpoint", "--root", str(project)])

            self.assertEqual(rc, 0)
            log = subprocess.run(["git", "log", "--oneline", "-1"], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
            self.assertIn("self_learn: advance to phase 1", log)
            self.assertTrue((project / "plans" / "done" / "3_plan.md").exists())
            self.assertTrue((project / "phase_1.md").exists())
            self.assertTrue((project / "docs" / "index.md").exists())
            self.assertTrue((project / "docs" / "phase-requirements.md").exists())
            self.assertTrue((project / "docs" / "phase-challenge.md").exists())
            self.assertTrue((project / "docs" / "modularity.md").exists())
            self.assertTrue((project / "docs" / "meta-trace.json").exists())
            self.assertTrue((project / "docs" / "meta-optimization.md").exists())
            self.assertTrue((project / "plans" / "done" / "6_plan.md").exists())
            self.assertTrue((project / "plans" / "7_plan.md").exists())

    def test_main_refresh_creates_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "plans" / "done").mkdir(parents=True)
            (root / "docs").mkdir(parents=True)
            (root / "plans" / "2_plan.md").write_text("status: active\n", encoding="utf-8")
            (root / "docs" / "learning-loop.md").write_text("# loop\n", encoding="utf-8")
            (root / "phase_0.md").write_text("""PROJECT PHASE 0\npurpose: entry point\ngoal: keep navigation clear\noutcome: docs index stays useful\ncore_requirements:\n- define the canonical project entry point.\n- keep the glossary and automation links visible.\n- preserve the phase boundary into phase 1.\nstatus: completed\n""", encoding="utf-8")
            (root / "phase_1.md").write_text("""PROJECT PHASE 1\npurpose: choose a next path\ngoal: suggest the next path\noutcome: ranked path\ncore_requirements:\n- define the first usable path candidates.\n- challenge each candidate with explicit criteria.\n- keep a review loop and feedback path.\nstatus: active\n""", encoding="utf-8")

            rc = sla.main(["refresh", "--root", str(root)])

            self.assertEqual(rc, 0)
            self.assertTrue((root / "docs" / "index.md").exists())
            self.assertTrue((root / "docs" / "glossary.md").exists())
            self.assertTrue((root / "docs" / "next-path.md").exists())
            self.assertTrue((root / "docs" / "phase-requirements.md").exists())
            self.assertTrue((root / "docs" / "phase-challenge.md").exists())
            self.assertTrue((root / "docs" / "modularity.md").exists())
            self.assertTrue((root / "docs" / "meta-trace.json").exists())
            self.assertTrue((root / "docs" / "meta-optimization.md").exists())
            index = (root / "docs" / "index.md").read_text(encoding="utf-8")
            self.assertIn("2_plan.md", index)
            self.assertIn("learning-loop.md", index)
            self.assertIn("glossary.md", index)
            self.assertIn("next-path.md", index)
            self.assertIn("phase-requirements.md", index)
            self.assertIn("phase-challenge.md", index)
            self.assertIn("modularity.md", index)

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
            self.assertEqual(report["modularity_budget"], [])

    def test_modularity_budget_flags_large_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            root.mkdir(parents=True)
            big = root / "big.md"
            big.write_text("\n".join(f"line {i}" for i in range(701)) + "\n", encoding="utf-8")

            issues = sla.modularity_budget(root)

            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0]["path"], "big.md")
            self.assertEqual(issues[0]["line_count"], 701)
            self.assertEqual(issues[0]["limit"], 700)

    def test_git_checkpoint_blocks_large_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            root.mkdir(parents=True)
            (root / "big.md").write_text("\n".join(f"line {i}" for i in range(701)) + "\n", encoding="utf-8")

            with self.assertRaises(RuntimeError):
                sla.git_checkpoint(root)

    def test_challenge_action_writes_phase_challenge(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "docs").mkdir(parents=True)
            (root / "phase_0.md").write_text("""PROJECT PHASE 0\npurpose: entry point\ngoal: keep navigation clear\noutcome: docs index stays useful\ncore_requirements:\n- define the canonical project entry point.\n- keep the glossary and automation links visible.\n- preserve the phase boundary into phase 1.\nstatus: completed\n""", encoding="utf-8")
            (root / "phase_1.md").write_text("""PROJECT PHASE 1\npurpose: choose a next path\ngoal: suggest the next path\noutcome: ranked path\ncore_requirements:\n- define the first usable path candidates.\n- challenge each candidate with explicit criteria.\n- keep a review loop and feedback path.\nstatus: active\n""", encoding="utf-8")

            rc = sla.main(["challenge", "--root", str(root)])

            self.assertEqual(rc, 0)
            self.assertTrue((root / "docs" / "phase-challenge.md").exists())
            challenge = (root / "docs" / "phase-challenge.md").read_text(encoding="utf-8")
            self.assertIn("Challenge the requirements for phase_0.md", challenge)
            self.assertIn("Challenge the requirements for phase_1.md", challenge)

    def test_refresh_meta_trace_json_is_machine_readable(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            root = repo / "prj" / "self_learn"
            (root / "plans" / "done").mkdir(parents=True)
            (root / "docs").mkdir(parents=True)
            (root / "plans" / "2_plan.md").write_text("status: active\n", encoding="utf-8")
            db = sqlite3.connect(repo / "continuity.db")
            db.execute("create table metacognitive_state(state_key text primary key, value text, version integer, updated_at text default current_timestamp)")
            db.commit()
            db.close()
            (root / "phase_0.md").write_text("""PROJECT PHASE 0
purpose: entry point
goal: keep navigation clear
outcome: docs index stays useful
core_requirements:
- define the canonical project entry point.
- keep the glossary and automation links visible.
- preserve the phase boundary into phase 1.
status: completed
""", encoding="utf-8")
            (root / "phase_1.md").write_text("""PROJECT PHASE 1
purpose: choose a next path
goal: suggest the next path
outcome: ranked path
core_requirements:
- define the first usable path candidates.
- challenge each candidate with explicit criteria.
- keep a review loop and feedback path.
status: active
""", encoding="utf-8")

            report = sla.refresh(root)
            payload = json.loads((root / "docs" / "meta-trace.json").read_text(encoding="utf-8"))

            self.assertTrue(payload["ready"])
            self.assertEqual(payload["version"], 1)
            self.assertIn("meta_trace", report)
            self.assertIn("meta_state", report)
            self.assertTrue(report["meta_state"]["updated"])

    def test_review_action_prints_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "docs").mkdir(parents=True)
            (root / "phase_0.md").write_text("""PROJECT PHASE 0\npurpose: entry point\ngoal: keep navigation clear\noutcome: docs index stays useful\ncore_requirements:\n- define the canonical project entry point.\n- keep the glossary and automation links visible.\n- preserve the phase boundary into phase 1.\nstatus: completed\n""", encoding="utf-8")
            (root / "phase_1.md").write_text("""PROJECT PHASE 1\npurpose: choose a next path\ngoal: suggest the next path\noutcome: ranked path\ncore_requirements:\n- define the first usable path candidates.\n- challenge each candidate with explicit criteria.\n- keep a review loop and feedback path.\nstatus: active\n""", encoding="utf-8")

            rc = sla.main(["review", "--root", str(root)])

            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
