import json
import shutil
import tempfile
import unittest
from pathlib import Path

import plan_command
import memory_command


class PlanCommandTests(unittest.TestCase):
    def test_plan_routes_are_registered(self):
        conn = plan_command.connect()
        try:
            status = conn.execute("select command_template from control_command_routes where route_name='plan_status'").fetchone()
            goal = conn.execute("select command_template from control_command_routes where route_name='plan_goal_set'").fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(status)
        self.assertIn('plan_command.py status', status[0])
        self.assertIsNotNone(goal)
        self.assertIn('plan_command.py goal set', goal[0])

    def test_set_primary_goal_updates_state_history_and_journal(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(plan_command.DB_PATH, db_copy)
            conn = plan_command.connect(db_copy)
            try:
                before = conn.execute(
                    "select value, version from metacognitive_state where state_key='primary_goal'"
                ).fetchone()
                version = plan_command.set_primary_goal(conn, 'Lightweight planning goal', reason='Need a persistent planning target')
                after = conn.execute(
                    "select value, version from metacognitive_state where state_key='primary_goal'"
                ).fetchone()
                history = conn.execute(
                    "select count(*) from metacognitive_state_history where state_key='primary_goal'"
                ).fetchone()[0]
                journal = conn.execute(
                    "select count(*) from journal where category='planning' and summary like 'Primary goal set to:%'"
                ).fetchone()[0]
                episode = conn.execute(
                    "select claim, evidence_summary from reasoning_episodes where title='Update primary goal' order by id desc limit 1"
                ).fetchone()
            finally:
                conn.close()

            self.assertNotEqual(before[0], after[0])
            self.assertEqual(after[0], 'Lightweight planning goal')
            self.assertEqual(version, after[1])
            self.assertGreaterEqual(history, 1)
            self.assertEqual(journal, 1)
            self.assertIsNotNone(episode)
            self.assertIn('Lightweight planning goal', episode[0])
            self.assertIn('Need a persistent planning target', episode[1])
        finally:
            shutil.rmtree(tmpdir)

    def test_status_orders_plans_by_priority(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(plan_command.DB_PATH, db_copy)
            conn = plan_command.connect(db_copy)
            try:
                plan_command.set_primary_goal(conn, 'Alpha priority goal')
                plan_command.start_plan(conn, 'alpha_plan', 'Alpha plan', 'This plan matches the Alpha priority goal.', status='active')
                plan_command.start_plan(conn, 'beta_plan', 'Beta plan', 'An unrelated plan with no goal overlap.', status='active')
                status = plan_command.planning_status(conn)
            finally:
                conn.close()

            self.assertGreaterEqual(status['active_plans'][0]['priority_score'], status['active_plans'][1]['priority_score'])
            self.assertEqual(status['active_plans'][0]['plan_key'], 'alpha_plan')
        finally:
            shutil.rmtree(tmpdir)

    def test_start_plan_add_step_and_status(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(plan_command.DB_PATH, db_copy)
            conn = plan_command.connect(db_copy)
            try:
                plan_command.set_primary_goal(conn, 'Lightweight planning goal')
                plan_command.start_plan(conn, 'lightweight_planning', 'Lightweight planning', 'Keep one goal, one active plan, and a few steps.', prompt='recallable_prompt_token', status='active')
                plan_command.add_step(conn, 'lightweight_planning', 'capture_goal', 'Capture the current goal in metacognitive state')
                plan_command.add_step(conn, 'lightweight_planning', 'track_steps', 'Track a short list of actionable steps')
                plan_command.set_step_status(conn, 'lightweight_planning', 'capture_goal', 'completed', evidence='Goal stored successfully')
                status = plan_command.planning_status(conn)
                plan_row = conn.execute(
                    "select status, title, prompt from work_plans where plan_key='lightweight_planning'"
                ).fetchone()
                step_rows = conn.execute(
                    "select step_key, status from work_plan_steps where plan_id=(select id from work_plans where plan_key='lightweight_planning') order by step_order"
                ).fetchall()
            finally:
                conn.close()

            self.assertEqual(plan_row[0], 'active')
            self.assertEqual(plan_row[2], 'recallable_prompt_token')
            self.assertEqual(status['primary_goal']['value'], 'Lightweight planning goal')
            self.assertEqual(status['active_plans'][0]['plan_key'], 'lightweight_planning')
            self.assertEqual(step_rows[0][0], 'capture_goal')
            self.assertEqual(step_rows[0][1], 'completed')
            self.assertEqual(step_rows[1][0], 'track_steps')
            self.assertEqual(step_rows[1][1], 'pending')
            self.assertGreaterEqual(len(status['active_plans'][0]['steps']), 2)
            self.assertEqual(status['active_plans'][0]['prompt'], 'recallable_prompt_token')
            recall = json.loads(memory_command.run_memory_recall('recallable_prompt_token', db_path=db_copy, layer='procedural'))
            self.assertGreaterEqual(recall['hit_count'], 1)
            self.assertEqual(recall['hits'][0]['source_type'], 'work_plan')
            self.assertEqual(recall['hits'][0]['source_key'], 'lightweight_planning')
        finally:
            shutil.rmtree(tmpdir)

    def test_synthesis_promotion_creates_policy_when_missing(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(plan_command.DB_PATH, db_copy)
            conn = plan_command.connect(db_copy)
            try:
                cur = conn.cursor()
                cur.execute(
                    "insert into syntheses(synthesis_key, topic, summary, claim, confidence, status, source_mode, metacognitive_note) values(?,?,?,?,?,?,?,?)",
                    ('policy_transfer_probe', 'Policy transfer probe', 'Policy transfer probe summary', 'Policy transfer probe claim', 0.93, 'active', 'derived', 'probe'),
                )
                result = plan_command.promote_synthesis_to_policy(conn, 'policy_transfer_probe')
                policy_row = conn.execute(
                    "select category, value, confidence, provenance, version from metacognitive_state where state_key='policy_transfer_probe'"
                ).fetchone()
                synthesis_row = conn.execute(
                    "select status from syntheses where synthesis_key='policy_transfer_probe'"
                ).fetchone()
            finally:
                conn.close()

            self.assertTrue(result['created'])
            self.assertEqual(result['policy_key'], 'policy_transfer_probe')
            self.assertEqual(policy_row[0], 'governance')
            self.assertEqual(policy_row[1], 'Policy transfer probe claim')
            self.assertEqual(policy_row[3], 'synthesis:policy_transfer_probe')
            self.assertEqual(synthesis_row[0], 'settled')
        finally:
            shutil.rmtree(tmpdir)

    def test_synthesis_promotion_keeps_existing_policy(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(plan_command.DB_PATH, db_copy)
            conn = plan_command.connect(db_copy)
            try:
                cur = conn.cursor()
                cur.execute(
                    "insert into syntheses(synthesis_key, topic, summary, claim, confidence, status, source_mode, metacognitive_note) values(?,?,?,?,?,?,?,?)",
                    ('policy_keep_probe', 'Policy keep probe', 'Policy keep probe summary', 'Policy keep probe claim', 0.91, 'active', 'derived', 'probe'),
                )
                cur.execute(
                    "insert into metacognitive_state(state_key, category, value, confidence, provenance, version) values(?,?,?,?,?,?)",
                    ('policy_keep_probe', 'governance', 'Existing policy text', 0.5, 'manual', 1),
                )
                result = plan_command.promote_synthesis_to_policy(conn, 'policy_keep_probe')
                policy_row = conn.execute(
                    "select category, value, confidence, provenance, version from metacognitive_state where state_key='policy_keep_probe'"
                ).fetchone()
                synthesis_row = conn.execute(
                    "select status from syntheses where synthesis_key='policy_keep_probe'"
                ).fetchone()
            finally:
                conn.close()

            self.assertFalse(result['created'])
            self.assertEqual(policy_row[1], 'Existing policy text')
            self.assertEqual(policy_row[2], 0.5)
            self.assertEqual(policy_row[3], 'manual')
            self.assertEqual(synthesis_row[0], 'settled')
        finally:
            shutil.rmtree(tmpdir)

    def test_block_step_creates_open_question(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(plan_command.DB_PATH, db_copy)
            conn = plan_command.connect(db_copy)
            try:
                plan_command.start_plan(conn, 'blocker_plan', 'Blocker plan', 'Demonstrate blocker handling.', status='active')
                plan_command.add_step(conn, 'blocker_plan', 'resolve_gap', 'Resolve the planning gap')
                before = conn.execute("select count(*) from open_questions").fetchone()[0]
                plan_command.block_step(conn, 'blocker_plan', 'resolve_gap', 'What is the missing dependency?')
                after = conn.execute("select count(*) from open_questions").fetchone()[0]
                latest = conn.execute(
                    "select question, status from open_questions order by id desc limit 1"
                ).fetchone()
                step = conn.execute(
                    "select status, evidence from work_plan_steps where plan_id=(select id from work_plans where plan_key='blocker_plan') and step_key='resolve_gap'"
                ).fetchone()
            finally:
                conn.close()

            self.assertEqual(after, before + 1)
            self.assertEqual(latest[0], 'What is the missing dependency?')
            self.assertEqual(latest[1], 'open')
            self.assertEqual(step[0], 'pending')
            self.assertIn('Blocked by question', step[1])
        finally:
            shutil.rmtree(tmpdir)


if __name__ == '__main__':
    unittest.main()
