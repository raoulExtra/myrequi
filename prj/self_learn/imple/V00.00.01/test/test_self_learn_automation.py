from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import self_learn_automation as sla
import self_learn_cli as cli
import self_learn_phase_2 as phase2
import self_learn_prompt as prompt_module

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

    def test_sync_promotes_prepared_active_plan_when_when_to_run_is_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "plans" / "prep").mkdir(parents=True)
            (root / "docs").mkdir(parents=True)
            (root / "plans" / "prep" / "7_plan.md").write_text("""# plan\nstatus: active\n\n## objective\nphase related work\n\n## when to run\n- run when a trigger is ready\n\n## steps\n1. do it\n""", encoding="utf-8")

            report = sla.sync(root)

            self.assertIn("plans/7_plan.md", report.moved_plans)
            self.assertTrue((root / "plans" / "7_plan.md").exists())
            self.assertFalse((root / "plans" / "prep" / "7_plan.md").exists())

    def test_trigger_next_phase_ai_suggests_next_phase_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "plans" / "prep").mkdir(parents=True)
            (root / "docs").mkdir(parents=True)
            (root / "plans" / "prep" / "7_plan.md").write_text("""# Self-learn meta optimization plan\nstatus: active\n\n## objective\nAutomate the trace of self-learning optimization so the project can see its own improvement signals.\n\n## when to run\n- run when a new active plan appears or an active plan changes.\n\n## steps\n1. Generate a meta optimization trace from phase state and modularity signals.\n2. Persist the trace in docs and continuity.db.\n3. Use the trace to guide the next self-learning review.\n4. Keep the trace format small and durable.\n""", encoding="utf-8")

            result = cli.main(["trigger", "next-phase-ai", "--root", str(root)])

            self.assertEqual(result, 0)
            handoff = (root / "docs" / "active-plan.md").read_text(encoding="utf-8")
            suggestion = (root / "docs" / "next-phase-generation.md").read_text(encoding="utf-8")
            self.assertIn("phase 0 purpose", suggestion)
            self.assertIn("phase 3", suggestion)
            self.assertIn("manual trigger CLI", suggestion)
            self.assertIn("active plans", handoff)
            self.assertIn("prep plans", suggestion)
            self.assertTrue((root / "plans" / "prep" / "7_plan.md").exists())
            self.assertFalse((root / "plans" / "7_plan.md").exists())

    def test_trigger_check_gloss_expands_current_phase_terms(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "docs").mkdir(parents=True)
            (root / "docs" / "glossary.md").write_text((Path("prj/self_learn/docs/glossary.md")).read_text(encoding="utf-8"), encoding="utf-8")
            (root / "phase_0.md").write_text("""PROJECT PHASE 0\npurpose: entry point\ngoal: keep navigation clear\noutcome: docs index stays useful\ncore_requirements:\n- define the canonical project entry point.\n- keep the glossary and automation links visible.\n- preserve the phase boundary into phase 1.\nstatus: completed\n""", encoding="utf-8")
            (root / "phase_1.md").write_text("""PROJECT PHASE 1\npurpose: choose a next path\ngoal: suggest the next path\noutcome: ranked path\ncore_requirements:\n- define the first usable path candidates.\n- challenge each candidate with explicit criteria.\n- keep a review loop and feedback path.\n- make the manual trigger CLI obvious.\nstatus: active\n""", encoding="utf-8")

            result = cli.main(["trigger", "check-gloss", "--root", str(root), "--expand"])

            self.assertEqual(result, 0)
            self.assertTrue((root / "docs" / "glossary-check.md").exists())
            expanded = (root / "docs" / "glossary-check.md").read_text(encoding="utf-8")
            self.assertIn("Glossary phase check", expanded)
            self.assertIn("manual trigger CLI", expanded)
            self.assertIn("new important term count", expanded)

    def test_trigger_prep_plan_promotes_specific_prepared_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "plans" / "prep").mkdir(parents=True)
            (root / "docs").mkdir(parents=True)
            (root / "plans" / "prep" / "7_plan.md").write_text("""# Self-learn meta optimization plan\nstatus: active\n\n## objective\nAutomate the trace of self-learning optimization so the project can see its own improvement signals.\n\n## when to run\n- run when a new active plan appears or an active plan changes.\n\n## steps\n1. Generate a meta optimization trace from phase state and modularity signals.\n2. Persist the trace in docs and continuity.db.\n3. Use the trace to guide the next self-learning review.\n4. Keep the trace format small and durable.\n""", encoding="utf-8")

            result = cli.main(["trigger", "prep-plan", "7", "--root", str(root)])

            self.assertEqual(result, 0)
            self.assertTrue((root / "plans" / "7_plan.md").exists())
            self.assertFalse((root / "plans" / "prep" / "7_plan.md").exists())

    def test_trigger_record_plan_creates_execution_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "plans").mkdir(parents=True)
            (root / "docs").mkdir(parents=True)
            plan = root / "plans" / "4_plan.md"
            plan.write_text("""# Self-learn AI next-path phase plan\nstatus: active\n\n## objective\nHave AI derive, score, and select self-learn paths from current project evidence, then write the chosen path into the phase 1 docs.\n\n## when to run\n- run when the path selection work is ready.\n\n## steps\n1. Derive at least three candidate paths from the current project state and glossary.\n2. Score each candidate with explicit criteria, costs, and risks.\n3. Select one winner and explain why it beats the others.\n4. Write the selected path and review context into `phase_1.md` and `docs/phase-1-outcome.md`.\n""", encoding="utf-8")

            result = cli.main(["trigger", "record-plan", "--root", str(root), "--plan", str(plan), "--summary", "manual run", "--detail", "step one", "--complete-source"])

            self.assertEqual(result, 0)
            done_dir = root / "plans" / "done"
            records = sorted(done_dir.glob("4_plan_exec_*.md"))
            self.assertTrue(records)
            self.assertTrue((done_dir / "4_plan.md").exists())
            self.assertFalse(plan.exists())
            self.assertIn("manual run", records[-1].read_text(encoding="utf-8"))

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
            self.assertTrue((root / "docs" / "working-rules.md").exists())
            self.assertTrue((root / "docs" / "meta-trace.json").exists())
            self.assertTrue((root / "docs" / "meta-optimization.md").exists())
            self.assertTrue((root / "docs" / "meta-actions.json").exists())
            self.assertTrue((root / "docs" / "meta-actions.md").exists())
            self.assertTrue((root / "docs" / "active-plan.md").exists())
            self.assertTrue((root / "docs" / "phase-0-entry.md").exists())
            self.assertTrue((root / "docs" / "phase-0-core-requi.md").exists())
            self.assertTrue((root / "docs" / "phase-0-core-review.md").exists())
            self.assertTrue((root / "docs" / "phase-0/auto/phase-0-core-requi-auto.md").exists())
            self.assertTrue((root / "docs" / "phase-0/auto/phase-0-core-review-auto.md").exists())
            auto_requirements = (root / "docs" / "phase-0/auto/phase-0-core-requi-auto.md").read_text(encoding="utf-8")
            self.assertIn("RC001-AUTO", auto_requirements)
            self.assertIn("RC001-AC001-AUTO", auto_requirements)
            self.assertIn("RC008-AUTO", auto_requirements)
            self.assertIn("RC008-AC002-AUTO", auto_requirements)
            self.assertIn("RC011-AUTO", auto_requirements)
            self.assertIn("RC011-AC008-AUTO", auto_requirements)
            self.assertNotIn("AUTO-RC008", auto_requirements)
            self.assertTrue((root / "docs" / "phase-1-next-path.md").exists())
            self.assertTrue((root / "docs" / "phase-1-core-requi.md").exists())
            self.assertTrue((root / "docs" / "phase-1-core-review.md").exists())
            self.assertTrue((root / "docs" / "phase-2-mission.md").exists())
            self.assertTrue((root / "docs" / "phase-2-core-requi.md").exists())
            self.assertTrue((root / "docs" / "phase-2-core-review.md").exists())
            self.assertIn("[code] PH000-RC001", (root / "phase_0.md").read_text(encoding="utf-8"))
            self.assertIn("[auto_ai] PH001-RC001", (root / "phase_1.md").read_text(encoding="utf-8"))
            self.assertIn("[auto_ai] PH002-RC001", (root / "phase_2.md").read_text(encoding="utf-8"))
            self.assertIn("phase_2_learning_path", report)
            self.assertEqual(report["phase_2_learning_path"]["selected"]["key"], "P2-C1")
            self.assertIn("docs/index.md", report["phase_2_learning_path"]["selected"]["files"])
            self.assertIn("docs/phase-requirements.md", report["phase_2_learning_path"]["selected"]["files"])
            self.assertIn("ranking:", (root / "phase_2.md").read_text(encoding="utf-8"))
            self.assertIn("derived_learning_path:", (root / "phase_2.md").read_text(encoding="utf-8"))
            self.assertIn("files:", (root / "phase_2.md").read_text(encoding="utf-8"))
            self.assertIn("named_phase_1", report)
            self.assertIn("named_phase_0", report)
            self.assertIn("phase_1_core_requi", report)
            self.assertIn("phase_1_core_review", report)
            active_plan_doc = (root / "docs" / "active-plan.md").read_text(encoding="utf-8")
            self.assertIn("2_plan.md", active_plan_doc)
            self.assertNotIn("1_plan.md", active_plan_doc)
            index = (root / "docs" / "index.md").read_text(encoding="utf-8")
            self.assertIn("learning-loop.md", index)
            self.assertIn("glossary.md", index)
            self.assertIn("next-path.md", index)
            self.assertIn("phase-requirements.md", index)
            self.assertIn("phase-challenge.md", index)
            self.assertIn("phase-0-entry.md", index)
            self.assertIn("phase-0-core-requi.md", index)
            self.assertIn("phase-0-core-review.md", index)
            self.assertIn("phase-1-next-path.md", index)
            self.assertIn("phase-1-core-requi.md", index)
            self.assertIn("phase-1-core-review.md", index)
            self.assertIn("phase-2-mission.md", index)
            self.assertIn("phase-2-core-requi.md", index)
            self.assertIn("phase-2-core-review.md", index)
            self.assertIn("modularity.md", index)
            self.assertIn("working-rules.md", index)
            self.assertIn("meta-actions.md", index)
            self.assertIn("active-plan.md", index)
            self.assertIn("meta-optimization.md", index)
            self.assertIn("2_plan.md", index)
            self.assertIn("1_plan.md", index)
            self.assertIn("docs_index", report)
            self.assertIn("phase_requirements_report", report)
            self.assertIn("phase_manifest", report)
            self.assertIn("phase_challenge_bundle", report)
            self.assertIn("active_plan_handoff", report)
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
            self.assertTrue((project / "phase_0.md").exists())
            self.assertTrue((project / "phase_1.md").exists())
            self.assertTrue((project / "docs" / "glossary.md").exists())
            self.assertTrue((project / "docs" / "next-path.md").exists())
            self.assertTrue((project / "docs" / "phase-requirements.md").exists())
            self.assertTrue((project / "docs" / "phase-challenge.md").exists())
            self.assertTrue((project / "docs" / "modularity.md").exists())
            self.assertTrue((project / "docs" / "working-rules.md").exists())
            self.assertTrue((project / "docs" / "meta-trace.json").exists())
            self.assertTrue((project / "docs" / "meta-optimization.md").exists())
            self.assertTrue((project / "docs" / "phase-0-entry.md").exists())
            self.assertTrue((project / "docs" / "phase-0-core-requi.md").exists())
            self.assertTrue((project / "docs" / "phase-0-core-review.md").exists())
            self.assertTrue((project / "docs" / "phase-1-next-path.md").exists())
            self.assertTrue((project / "docs" / "phase-1-core-requi.md").exists())
            self.assertTrue((project / "docs" / "phase-1-core-review.md").exists())
            self.assertTrue((project / "docs" / "phase-2-mission.md").exists())
            self.assertTrue((project / "docs" / "phase-2-core-requi.md").exists())
            self.assertTrue((project / "docs" / "phase-2-core-review.md").exists())
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
            self.assertTrue((project / "docs" / "working-rules.md").exists())
            self.assertTrue((project / "docs" / "meta-trace.json").exists())
            self.assertTrue((project / "docs" / "meta-optimization.md").exists())
            self.assertTrue((project / "docs" / "phase-0-entry.md").exists())
            self.assertTrue((project / "docs" / "phase-0-core-requi.md").exists())
            self.assertTrue((project / "docs" / "phase-0-core-review.md").exists())
            self.assertTrue((project / "docs" / "phase-1-next-path.md").exists())
            self.assertTrue((project / "docs" / "phase-1-core-requi.md").exists())
            self.assertTrue((project / "docs" / "phase-1-core-review.md").exists())
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
            self.assertTrue((root / "docs" / "working-rules.md").exists())
            self.assertTrue((root / "docs" / "meta-trace.json").exists())
            self.assertTrue((root / "docs" / "meta-optimization.md").exists())
            self.assertTrue((root / "docs" / "phase-0-entry.md").exists())
            self.assertTrue((root / "docs" / "phase-0-core-requi.md").exists())
            self.assertTrue((root / "docs" / "phase-0-core-review.md").exists())
            self.assertTrue((root / "docs" / "phase-0/auto/phase-0-core-requi-auto.md").exists())
            self.assertTrue((root / "docs" / "phase-0/auto/phase-0-core-review-auto.md").exists())
            auto_review = (root / "docs" / "phase-0/auto/phase-0-core-review-auto.md").read_text(encoding="utf-8")
            self.assertIn("RC001-AUTO", auto_review)
            self.assertIn("RC001-AC001-AUTO", auto_review)
            self.assertIn("RC008-AUTO", auto_review)
            self.assertIn("RC011-AUTO", auto_review)
            self.assertIn("RC011-AC008-AUTO", auto_review)
            self.assertNotIn("AUTO-RC008", auto_review)
            self.assertTrue((root / "docs" / "phase-1-next-path.md").exists())
            self.assertTrue((root / "docs" / "phase-1-core-requi.md").exists())
            self.assertTrue((root / "docs" / "phase-1-core-review.md").exists())
            self.assertIn("[code] PH000-RC001", (root / "docs" / "phase-0-core-requi.md").read_text(encoding="utf-8"))
            self.assertIn("[auto_ai] PH001-RC001", (root / "docs" / "phase-1-core-requi.md").read_text(encoding="utf-8"))
            self.assertIn("[auto_ai] PH002-RC001", (root / "docs" / "phase-2-core-requi.md").read_text(encoding="utf-8"))
            self.assertIn("first concrete automation learning path", (root / "docs" / "phase-2-core-requi.md").read_text(encoding="utf-8"))
            self.assertIn("derived candidate paths", (root / "docs" / "phase-2-mission.md").read_text(encoding="utf-8"))
            self.assertIn("ranking", (root / "docs" / "phase-2-mission.md").read_text(encoding="utf-8"))
            self.assertIn("current automation mission", (root / "docs" / "phase-2-mission.md").read_text(encoding="utf-8"))
            self.assertIn("[auto_ai] PH002-RC001", (root / "phase_2.md").read_text(encoding="utf-8"))
            self.assertIn("files:", (root / "phase_2.md").read_text(encoding="utf-8"))
            self.assertIn("status: active", (root / "phase_2.md").read_text(encoding="utf-8"))
            index = (root / "docs" / "index.md").read_text(encoding="utf-8")
            self.assertIn("2_plan.md", index)
            self.assertIn("learning-loop.md", index)
            self.assertIn("glossary.md", index)
            self.assertIn("next-path.md", index)
            self.assertIn("phase-requirements.md", index)
            self.assertIn("phase-challenge.md", index)
            self.assertIn("phase-1-next-path.md", index)
            self.assertIn("phase-1-core-requi.md", index)
            self.assertIn("phase-1-core-review.md", index)
            self.assertIn("phase-2-mission.md", index)
            self.assertIn("phase-2-core-requi.md", index)
            self.assertIn("phase-2-core-review.md", index)
            self.assertIn("modularity.md", index)
            self.assertIn("working-rules.md", index)

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
            self.assertTrue(payload["corrections"])
            self.assertIn(payload["corrections"][0]["kind"], {"auto-heal", "preventive"})
            self.assertIn("meta_trace", report)
            self.assertIn("meta_state", report)
            self.assertTrue(report["meta_state"]["updated"])

    def test_phase_2_selection_ranks_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_report = [
                {"phase": "phase_0.md", "purpose": "entry", "goal": "goal0", "outcome": "out0", "status": "completed", "core_requirements": ["a", "b", "c"], "missing": []},
                {"phase": "phase_1.md", "purpose": "select", "goal": "goal1", "outcome": "out1", "status": "active", "core_requirements": ["a", "b", "c"], "missing": []},
            ]
            packet = phase2.select_phase_2_mission(phase_report)
            self.assertEqual(packet["selected"]["key"], "P2-C1")
            self.assertGreater(packet["selected"]["score"], packet["ranked_candidates"][1]["score"])
            self.assertIn("derive the next automation mission", packet["outcome"])

    def test_review_action_prints_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "docs").mkdir(parents=True)
            (root / "phase_0.md").write_text("""PROJECT PHASE 0\npurpose: entry point\ngoal: keep navigation clear\noutcome: docs index stays useful\ncore_requirements:\n- define the canonical project entry point.\n- keep the glossary and automation links visible.\n- preserve the phase boundary into phase 1.\nstatus: completed\n""", encoding="utf-8")
            (root / "phase_1.md").write_text("""PROJECT PHASE 1\npurpose: choose a next path\ngoal: suggest the next path\noutcome: ranked path\ncore_requirements:\n- define the first usable path candidates.\n- challenge each candidate with explicit criteria.\n- keep a review loop and feedback path.\nstatus: active\n""", encoding="utf-8")

            rc = sla.main(["review", "--root", str(root)])

            self.assertEqual(rc, 0)

    def test_ask_command_returns_json_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "docs").mkdir(parents=True)

            with mock.patch("self_learn_cli.prompt.sys.stdin.isatty", return_value=True):
                with mock.patch("self_learn_cli.prompt.input", return_value="1"):
                    rc = cli.main(["ask", "Continue?", "--options", "yes,no", "--root", str(root)])

            self.assertEqual(rc, 0)

    def test_ask_command_uses_default_when_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "docs").mkdir(parents=True)

            with mock.patch("self_learn_cli.prompt.sys.stdin.isatty", return_value=True):
                with mock.patch("self_learn_cli.prompt.input", return_value=""):
                    rc = cli.main(["ask", "Continue?", "--default", "yes", "--root", str(root)])

            self.assertEqual(rc, 0)

    def test_ask_non_interactive_reads_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "docs").mkdir(parents=True)

            with mock.patch.dict(os.environ, {"SELF_LEARN_ANSWER": "maybe"}):
                with mock.patch("self_learn_cli.prompt.sys.stdin.isatty", return_value=False):
                    rc = cli.main(["ask", "Continue?", "--root", str(root)])

            self.assertEqual(rc, 0)

    def test_ask_non_interactive_falls_back_to_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "self_learn"
            (root / "docs").mkdir(parents=True)

            with mock.patch("self_learn_cli.prompt.sys.stdin.isatty", return_value=False):
                rc = cli.main(["ask", "Continue?", "--default", "yes", "--root", str(root)])

            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
