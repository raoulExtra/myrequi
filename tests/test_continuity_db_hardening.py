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

        self.assertEqual(
            rows,
            [
                ('belief_versions', 'history', 'append_only'),
                ('beliefs', 'current', 'mutable'),
                ('concept_links', 'evidence', 'append_only'),
                ('concepts', 'current', 'mutable'),
                ('continuity_requirement_versions', 'history', 'append_only'),
                ('continuity_requirements', 'current', 'mutable'),
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
                ('syntheses', 'current', 'mutable'),
                ('synthesis_conflicts', 'audit', 'append_only'),
                ('synthesis_inputs', 'evidence', 'append_only'),
                ('v_concept_links', 'derived', 'derived'),
                ('v_concepts', 'derived', 'derived'),
                ('v_interpreted_layer', 'derived', 'derived'),
                ('v_meaningful_sentences', 'derived', 'derived'),
                ('v_memory_index', 'derived', 'derived'),
                ('v_object_epistemic_tags', 'derived', 'derived'),
                ('v_syntheses', 'derived', 'derived'),
                ('v_synthesis_conflicts', 'derived', 'derived'),
                ('v_synthesis_inputs', 'derived', 'derived'),
                ('v_work_plan_links', 'derived', 'derived'),
                ('work_plan_links', 'derived', 'append_only'),
                ('work_plan_steps', 'current', 'mutable'),
                ('work_plans', 'current', 'mutable'),
            ],
        )

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
        self.assertIn('memory_index', concepts)
        self.assertIn('object_metadata', concepts)
        self.assertIn('metacognitive_state', concepts)
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
