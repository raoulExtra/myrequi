import shutil
import tempfile
import unittest
from pathlib import Path

import harden_continuity_db as hardening


class ContinuityDbHardeningTests(unittest.TestCase):
    def test_current_database_passes_validation(self):
        conn = hardening.connect()
        try:
            issues = hardening.validate(conn)
        finally:
            conn.close()

        self.assertEqual(issues, [])

    def test_contract_map_is_present(self):
        conn = hardening.connect()
        try:
            rows = conn.execute(
                "select table_name, role, write_mode from continuity_table_contracts order by table_name"
            ).fetchall()
        finally:
            conn.close()

        expected = [
            ('belief_versions', 'history', 'append_only'),
            ('beliefs', 'current', 'mutable'),
            ('concept_links', 'evidence', 'append_only'),
            ('concepts', 'current', 'mutable'),
            ('continuity_requirement_versions', 'history', 'append_only'),
            ('continuity_requirements', 'current', 'mutable'),
            ('decision_versions', 'history', 'append_only'),
            ('decision_options', 'current', 'mutable'),
            ('decisions', 'current', 'mutable'),
            ('epistemic_receipts', 'audit', 'immutable'),
            ('epistemic_tags', 'current', 'mutable'),
            ('ethical_action_checks', 'evidence', 'append_only'),
            ('ethical_principles', 'current', 'mutable'),
            ('feature_flag_events', 'audit', 'append_only'),
            ('feature_flags', 'current', 'mutable'),
            ('metacognitive_state', 'current', 'mutable'),
            ('metacognitive_state_history', 'history', 'append_only'),
            ('object_epistemic_tags', 'evidence', 'append_only'),
            ('object_metadata', 'current', 'mutable'),
            ('object_provenance', 'evidence', 'mutable'),
            ('open_questions', 'current', 'mutable'),
            ('reasoning_episode_inputs', 'evidence', 'append_only'),
            ('reasoning_episodes', 'current', 'mutable'),
            ('syntheses', 'current', 'mutable'),
            ('synthesis_conflicts', 'audit', 'append_only'),
            ('synthesis_inputs', 'evidence', 'append_only'),
            ('v_concept_links', 'derived', 'derived'),
            ('v_concepts', 'derived', 'derived'),
            ('v_decision_versions', 'derived', 'derived'),
            ('v_decision_options', 'derived', 'derived'),
            ('v_explain', 'derived', 'derived'),
            ('v_interpreted_layer', 'derived', 'derived'),
            ('v_item_links', 'derived', 'derived'),
            ('v_items', 'derived', 'derived'),
            ('v_meaningful_sentences', 'derived', 'derived'),
            ('v_memory_index', 'derived', 'derived'),
            ('v_meta', 'derived', 'derived'),
            ('v_object_epistemic_tags', 'derived', 'derived'),
            ('v_open_question_flow', 'derived', 'derived'),
            ('v_reasoning_episode_inputs', 'derived', 'derived'),
            ('v_reasoning_flow', 'derived', 'derived'),
            ('v_recall', 'derived', 'derived'),
            ('v_syntheses', 'derived', 'derived'),
            ('v_synthesis_conflicts', 'derived', 'derived'),
            ('v_synthesis_inputs', 'derived', 'derived'),
            ('v_work_plan_links', 'derived', 'derived'),
            ('work_plan_links', 'derived', 'append_only'),
            ('work_plan_steps', 'current', 'mutable'),
            ('work_plans', 'current', 'mutable'),
        ]
        self.assertEqual(rows, expected)

    def test_storage_map_view_is_present(self):
        conn = hardening.connect()
        try:
            rows = conn.execute(
                "select concept, storage_role, current_table, history_table from v_storage_map order by concept"
            ).fetchall()
        finally:
            conn.close()

        concepts = [row[0] for row in rows]
        self.assertIn('belief', concepts)
        self.assertIn('dream_session', concepts)
        self.assertIn('epistemic_receipt', concepts)
        self.assertIn('feature_flag', concepts)
        self.assertIn('interpreted_layer', concepts)
        self.assertIn('decision_history', concepts)
        self.assertIn('open_question_flow', concepts)
        self.assertIn('reasoning_flow', concepts)
        self.assertIn('item_link', concepts)
        self.assertIn('memory_index', concepts)
        self.assertIn('object_metadata', concepts)
        self.assertIn('raw_item', concepts)
        self.assertIn('metacognitive_state', concepts)
        self.assertIn('recall', concepts)
        self.assertIn('synthesis', concepts)
        self.assertIn('synthesis_input', concepts)
        self.assertIn('synthesis_conflict', concepts)
        self.assertGreaterEqual(len(rows), 10)

    def test_ethics_map_includes_fairness(self):
        conn = hardening.connect()
        try:
            row = conn.execute(
                "select principle_key, principle_kind, check_key, question from v_ethics_principles_map where principle_key='fairness' and check_key='fairness'"
            ).fetchone()
            hard_row = conn.execute(
                "select principle_key, check_key, hard_gate, question from v_ethics_principle_checks where principle_key='fairness' and check_key='unjust_disparate_treatment'"
            ).fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], 'fairness')
        self.assertEqual(row[2], 'fairness')
        self.assertIn('unfair', row[3].lower())
        self.assertIsNotNone(hard_row)
        self.assertEqual(hard_row[0], 'fairness')
        self.assertEqual(hard_row[1], 'unjust_disparate_treatment')
        self.assertEqual(hard_row[2], 1)
        self.assertIn('comparable', hard_row[3].lower())

    def test_interpreted_layer_is_seeded(self):
        conn = hardening.connect()
        try:
            row = conn.execute(
                "select synthesis_key, topic, input_count, unresolved_conflicts from v_interpreted_layer order by synthesis_key limit 1"
            ).fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(row)
        self.assertGreaterEqual(row[2], 1)
        self.assertEqual(row[3], 0)

    def test_reasoning_surface_includes_arguments_and_episodes(self):
        conn = hardening.connect()
        try:
            argument_count = conn.execute("select count(*) from arguments").fetchone()[0]
            argument_surface = conn.execute("select count(*) from v_items where item_kind='argument'").fetchone()[0]
            episode_count = conn.execute("select count(*) from reasoning_episodes").fetchone()[0]
            episode_surface = conn.execute("select count(*) from v_items where item_kind='reasoning_episode'").fetchone()[0]
        finally:
            conn.close()

        self.assertEqual(argument_surface, argument_count)
        self.assertEqual(episode_surface, episode_count)
        self.assertGreaterEqual(episode_count, 1)

    def test_argument_can_support_multiple_claims(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(hardening.DB_PATH, db_copy)
            conn = hardening.sqlite3.connect(db_copy)
            conn.execute('PRAGMA foreign_keys = ON')
            cur = conn.cursor()
            argument_id = cur.execute('select id from arguments order by id limit 1').fetchone()[0]
            cur.execute("insert into beliefs(slug,current_statement,confidence,status,current_version) values(?,?,?,?,?)", ('multi_claim_belief_one', 'first extra claim', 0.9, 'active', 1))
            cur.execute("insert into beliefs(slug,current_statement,confidence,status,current_version) values(?,?,?,?,?)", ('multi_claim_belief_two', 'second extra claim', 0.9, 'active', 1))
            belief_one = cur.execute("select id from beliefs where slug='multi_claim_belief_one'").fetchone()[0]
            belief_two = cur.execute("select id from beliefs where slug='multi_claim_belief_two'").fetchone()[0]
            cur.execute(
                "insert into argument_claim_links(argument_id, belief_id, relation, strength, note) values(?,?,?,?,?)",
                (argument_id, belief_one, 'supports', 0.7, 'extra supported claim one'),
            )
            cur.execute(
                "insert into argument_claim_links(argument_id, belief_id, relation, strength, note) values(?,?,?,?,?)",
                (argument_id, belief_two, 'supports', 0.6, 'extra supported claim two'),
            )
            conn.commit()
            claim_rows = cur.execute(
                'select belief_id, relation from v_argument_claims where argument_id=? order by belief_id',
                (argument_id,),
            ).fetchall()
            conn.close()

            self.assertGreaterEqual(len(claim_rows), 3)
            relations = {row[1] for row in claim_rows}
            self.assertIn('primary', relations)
            self.assertIn('supports', relations)
        finally:
            shutil.rmtree(tmpdir)

    def test_decision_history_is_backfilled_from_receipts(self):
        conn = hardening.connect()
        try:
            decision_receipts = conn.execute("select count(*) from epistemic_receipts where object_type='decision'").fetchone()[0]
            decision_versions = conn.execute("select count(*) from decision_versions").fetchone()[0]
            sample = conn.execute("select decision_id, version, source_receipt_id, decision from v_decision_versions order by decision_id, version limit 1").fetchone()
        finally:
            conn.close()

        self.assertEqual(decision_versions, decision_receipts)
        self.assertIsNotNone(sample)
        self.assertGreaterEqual(sample[1], 1)
        self.assertIsNotNone(sample[2])

    def test_reasoning_flow_is_formalized(self):
        conn = hardening.connect()
        try:
            input_count = conn.execute("select count(*) from reasoning_episode_inputs").fetchone()[0]
            flow = conn.execute("select episode_key, evidence_count, open_question_id, decision_id from v_reasoning_flow where evidence_count > 0 order by id limit 2").fetchall()
            decision_link = conn.execute("select id, decision, origin_reasoning_episode_id from decisions where origin_reasoning_episode_id is not null order by id limit 1").fetchone()
        finally:
            conn.close()

        self.assertGreaterEqual(input_count, 2)
        self.assertGreaterEqual(len(flow), 1)
        self.assertGreaterEqual(flow[0][1], 1)
        self.assertIsNotNone(decision_link)
        self.assertIsNotNone(decision_link[2])

    def test_open_question_flow_is_seeded_from_reasoning(self):
        conn = hardening.connect()
        try:
            seeded = conn.execute(
                "select count(*) from open_questions where origin_reasoning_episode_id is not null"
            ).fetchone()[0]
            expected = conn.execute(
                "select count(*) from reasoning_episodes where resolves_open_question_id is null and (coalesce(trim(uncertainty), '') <> '' or coalesce(trim(rejected_alternatives), '') <> '')"
            ).fetchone()[0]
            sample = conn.execute(
                "select question, status, origin_reasoning_episode_id from v_open_question_flow where origin_reasoning_episode_id is not null order by id limit 1"
            ).fetchone()
        finally:
            conn.close()

        self.assertEqual(seeded, expected)
        self.assertIsNotNone(sample)
        self.assertEqual(sample[1], 'open')
        self.assertIsNotNone(sample[2])

    def test_receipt_kinds_are_explicit(self):
        conn = hardening.connect()
        try:
            rows = dict(
                conn.execute(
                    "select receipt_kind, count(*) from epistemic_receipts group by receipt_kind order by receipt_kind"
                ).fetchall()
            )
        finally:
            conn.close()

        self.assertEqual(set(rows), {'object', 'provenance', 'snapshot'})
        self.assertGreater(rows['object'], 0)
        self.assertGreater(rows['provenance'], 0)
        self.assertGreater(rows['snapshot'], 0)

    def test_versioned_tables_are_enforced_on_temp_copy(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(hardening.DB_PATH, db_copy)
            conn = hardening.sqlite3.connect(db_copy)
            conn.execute('PRAGMA foreign_keys = ON')
            cur = conn.cursor()
            cur.execute("insert into beliefs(slug,current_statement,confidence,status,current_version) values(?,?,?,?,?)", ('temp_guard_test', 'temp', 0.5, 'active', 1))
            conn.commit()
            belief_id = cur.execute("select id from beliefs where slug='temp_guard_test'").fetchone()[0]
            seeded = cur.execute('select count(*) from belief_versions where belief_id=?', (belief_id,)).fetchone()[0]
            self.assertEqual(seeded, 1)
            with self.assertRaises(Exception):
                cur.execute('update belief_versions set statement=? where belief_id=?', ('x', belief_id))
                conn.commit()
            with self.assertRaises(Exception):
                cur.execute('update beliefs set current_statement=? where id=?', ('changed', belief_id))
                conn.commit()
            conn.close()
        finally:
            shutil.rmtree(tmpdir)


if __name__ == '__main__':
    unittest.main()
