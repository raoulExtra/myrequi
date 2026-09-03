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
            ('conviction_inputs', 'evidence', 'append_only'),
            ('conviction_versions', 'history', 'append_only'),
            ('convictions', 'current', 'mutable'),
            ('concept_links', 'evidence', 'append_only'),
            ('concepts', 'current', 'mutable'),
            ('continuity_requirement_versions', 'history', 'append_only'),
            ('continuity_requirements', 'current', 'mutable'),
            ('decision_options', 'current', 'mutable'),
            ('decision_versions', 'history', 'append_only'),
            ('decisions', 'current', 'mutable'),
            ('epistemic_receipts', 'audit', 'immutable'),
            ('epistemic_tags', 'current', 'mutable'),
            ('ethical_action_checks', 'evidence', 'append_only'),
            ('ethical_principles', 'current', 'mutable'),
            ('feature_flag_events', 'audit', 'append_only'),
            ('feature_flags', 'current', 'mutable'),
            ('component_influence_modes', 'current', 'mutable'),
            ('component_influence', 'current', 'mutable'),
            ('component_influence_presets', 'current', 'mutable'),
            ('component_influence_history', 'history', 'append_only'),
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
            ('v_convictions', 'derived', 'derived'),
            ('v_decision_options', 'derived', 'derived'),
            ('v_decision_patterns', 'derived', 'derived'),
            ('v_decision_versions', 'derived', 'derived'),
            ('v_entry_points', 'derived', 'derived'),
            ('v_explain', 'derived', 'derived'),
            ('v_interpreted_layer', 'derived', 'derived'),
            ('v_item_links', 'derived', 'derived'),
            ('v_items', 'derived', 'derived'),
            ('v_lean_thinking_patterns', 'derived', 'derived'),
            ('v_meaningful_sentences', 'derived', 'derived'),
            ('v_memory_index', 'derived', 'derived'),
            ('v_schema_catalog', 'derived', 'derived'),
            ('v_tag_search', 'derived', 'derived'),
            ('v_component_influence', 'derived', 'derived'),
            ('v_component_influence_history', 'derived', 'derived'),
            ('v_component_influence_modes', 'derived', 'derived'),
            ('v_component_influence_presets', 'derived', 'derived'),
            ('v_core_model', 'derived', 'derived'),
            ('v_meta', 'derived', 'derived'),
            ('v_object_epistemic_tags', 'derived', 'derived'),
            ('v_open_question_flow', 'derived', 'derived'),
            ('v_problem_solving_patterns', 'derived', 'derived'),
            ('v_problem_understanding_patterns', 'derived', 'derived'),
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
        self.assertEqual(set(rows), set(expected))

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
        self.assertIn('conviction', concepts)
        self.assertIn('core_model', concepts)
        self.assertIn('dream_session', concepts)
        self.assertIn('epistemic_receipt', concepts)
        self.assertIn('entry_points', concepts)
        self.assertIn('feature_flag', concepts)
        self.assertIn('interpreted_layer', concepts)
        self.assertIn('decision_history', concepts)
        self.assertIn('open_question_flow', concepts)
        self.assertIn('reasoning_flow', concepts)
        self.assertIn('item_link', concepts)
        self.assertIn('memory_index', concepts)
        self.assertIn('object_metadata', concepts)
        self.assertIn('raw_item', concepts)
        self.assertIn('schema_catalog', concepts)
        self.assertIn('metacognitive_state', concepts)
        self.assertIn('policy', concepts)
        self.assertIn('recall', concepts)
        self.assertIn('synthesis', concepts)
        self.assertIn('synthesis_input', concepts)
        self.assertIn('synthesis_conflict', concepts)
        self.assertGreaterEqual(len(rows), 10)

    def test_core_model_view_summarizes_four_layers(self):
        conn = hardening.connect()
        try:
            rows = conn.execute(
                "select layer_key, current_tables, collapsed_concepts from v_core_model order by sort_order"
            ).fetchall()
        finally:
            conn.close()

        self.assertEqual([row[0] for row in rows], ['state', 'action', 'audit', 'policy'])
        self.assertTrue(any('beliefs' in row[1] and 'convictions' in row[2] for row in rows if row[0] == 'state'))
        self.assertTrue(any('work_plans' in row[1] and 'plans' in row[2] for row in rows if row[0] == 'action'))
        self.assertTrue(any('epistemic_receipts' in row[1] and 'episodes' in row[2] for row in rows if row[0] == 'audit'))
        self.assertTrue(any('metacognitive_state' in row[1] and 'persona' in row[2] for row in rows if row[0] == 'policy'))

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
                "select synthesis_key, topic, input_count, unresolved_conflicts from v_interpreted_layer where input_count > 0 order by input_count desc, synthesis_key limit 1"
            ).fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(row)
        self.assertGreaterEqual(row[2], 1)

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

    def test_reasoning_pattern_reuse_claim_has_argument(self):
        conn = hardening.connect()
        try:
            belief_id = conn.execute(
                "select id from beliefs where slug='reasoning_pattern_reuse_improves_thinking'"
            ).fetchone()[0]
            argument_count = conn.execute(
                "select count(*) from arguments where belief_id=?",
                (belief_id,),
            ).fetchone()[0]
            primary_claim = conn.execute(
                "select relation from v_argument_claims where belief_slug='reasoning_pattern_reuse_improves_thinking' and relation='primary'"
            ).fetchone()
        finally:
            conn.close()

        self.assertGreaterEqual(argument_count, 1)
        self.assertIsNotNone(primary_claim)

    def test_core_thinking_patterns_are_stored(self):
        conn = hardening.connect()
        try:
            concept_rows = conn.execute(
                "select concept_key from concepts where concept_key in ('failure_mode_scan','decision_option_comparison','hypothesis_test_update') order by concept_key"
            ).fetchall()
            req_rows = conn.execute(
                "select requirement_key from continuity_requirements where requirement_key in ('CDB-13.10','CDB-13.11','CDB-13.12') order by requirement_key"
            ).fetchall()
            plan_row = conn.execute(
                "select plan_key from work_plans where plan_key='core_thinking_patterns'"
            ).fetchone()
            error_plan = conn.execute(
                "select id, title, objective, status from work_plans where plan_key='error_recovery_influence_flow'"
            ).fetchone()
            error_steps = conn.execute(
                "select step_order, step_key, status from work_plan_steps where plan_id=(select id from work_plans where plan_key='error_recovery_influence_flow') order by step_order"
            ).fetchall()
            error_links = conn.execute(
                "select concept_key, object_key from concept_links where object_type='work_plan' and object_key='error_recovery_influence_flow' order by concept_key"
            ).fetchall()
            demo_plan = conn.execute(
                "select id, title, objective, status from work_plans where plan_key='evolved_baseline_demo'"
            ).fetchone()
            demo_steps = conn.execute(
                "select step_order, step_key, status from work_plan_steps where plan_id=(select id from work_plans where plan_key='evolved_baseline_demo') order by step_order"
            ).fetchall()
            demo_links = conn.execute(
                "select concept_key, object_key from concept_links where object_type='work_plan' and object_key='evolved_baseline_demo' order by concept_key"
            ).fetchall()
            episode_row = conn.execute(
                "select episode_key from reasoning_episodes where episode_key='core_thinking_patterns_20260831100000'"
            ).fetchone()
        finally:
            conn.close()

        self.assertEqual([r[0] for r in concept_rows], ['decision_option_comparison', 'failure_mode_scan', 'hypothesis_test_update'])
        self.assertEqual([r[0] for r in req_rows], ['CDB-13.10', 'CDB-13.11', 'CDB-13.12'])
        self.assertIsNotNone(plan_row)
        self.assertIsNotNone(error_plan)
        self.assertEqual(error_plan[1], 'Error recovery influence flow')
        self.assertEqual(error_plan[3], 'active')
        self.assertEqual([r[1] for r in error_steps], ['detect', 'stabilize', 'inspect', 'correct', 'resume'])
        self.assertGreaterEqual(len(error_links), 10)
        self.assertIsNotNone(demo_plan)
        self.assertEqual(demo_plan[1], 'Evolved baseline demo')
        self.assertEqual(demo_plan[3], 'active')
        self.assertEqual([r[1] for r in demo_steps], ['compare', 'confirm', 'recover', 'learn', 'resync'])
        self.assertGreaterEqual(len(demo_links), 8)
        self.assertIsNotNone(episode_row)

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

    def test_entry_points_view_surfaces_current_items(self):
        conn = hardening.connect()
        try:
            rows = conn.execute(
                "select distinct entry_kind, entry_role from v_entry_points"
            ).fetchall()
        finally:
            conn.close()

        self.assertGreaterEqual(len(rows), 1)
        kinds = {row[0] for row in rows}
        self.assertTrue({'decision', 'work_plan', 'open_question'} & kinds)
        roles = {row[1] for row in rows}
        self.assertTrue({'actionable', 'analysis', 'context'} & roles)

    def test_discovery_and_canonicalization_concepts_are_seeded(self):
        conn = hardening.connect()
        try:
            discovery = conn.execute(
                "select name, description from concepts where concept_key='discovery'"
            ).fetchone()
            system_concept = conn.execute(
                "select name, description from concepts where concept_key='system'"
            ).fetchone()
            influence_concept = conn.execute(
                "select name, description from concepts where concept_key='influence'"
            ).fetchone()
            overlap = conn.execute(
                "select name, description from concepts where concept_key='overlap_reduction'"
            ).fetchone()
            schema = conn.execute(
                "select name, description from concepts where concept_key='schema_catalog'"
            ).fetchone()
            canonical = conn.execute(
                "select name, description from concepts where concept_key='canonical_home_enforcement'"
            ).fetchone()
            links = conn.execute(
                "select concept_key, object_key from concept_links where object_type='work_plan' and concept_key='discovery' order by object_key"
            ).fetchall()
            db_links = conn.execute(
                "select concept_key, object_type, object_key, relation from concept_links where concept_key in ('system','canonical_home_enforcement','overlap_reduction','schema_catalog','entrypoint','correction') order by concept_key, object_key"
            ).fetchall()
            tag_rows = conn.execute(
                "select tag_key, label from epistemic_tags where tag_key in ('persona','system','trait') order by tag_key"
            ).fetchall()
            persona_tagged = conn.execute(
                "select count(*) from object_epistemic_tags where tag_key='persona' and object_type='metacognitive_state'"
            ).fetchone()[0]
            system_tagged = conn.execute(
                "select count(*) from object_epistemic_tags where tag_key='system' and object_type='metacognitive_state' and object_key like 'persona_%'"
            ).fetchone()[0]
            trait_tagged = conn.execute(
                "select count(*) from object_epistemic_tags where tag_key='trait' and object_type='metacognitive_state' and object_key like 'persona_%'"
            ).fetchone()[0]
            system_concept_tagged = conn.execute(
                "select count(*) from object_epistemic_tags where tag_key='system' and object_type='concept' and object_key='system'"
            ).fetchone()[0]
            influence_tagged = conn.execute(
                "select count(*) from object_epistemic_tags where object_type='concept' and object_key='influence' and tag_key in ('epistemic:reasoning','epistemic:state','epistemic:constraint')"
            ).fetchone()[0]
            persona = conn.execute(
                "select label, description from epistemic_tags where tag_key='persona'"
            ).fetchone()
            system = conn.execute(
                "select label, description from epistemic_tags where tag_key='system'"
            ).fetchone()
            trait = conn.execute(
                "select label, description from epistemic_tags where tag_key='trait'"
            ).fetchone()
            persona_count = conn.execute(
                "select count(*) from object_epistemic_tags where tag_key='persona' and object_type='metacognitive_state'"
            ).fetchone()[0]
            persona_system_analyst_tags = conn.execute(
                "select object_key, tag_key from object_epistemic_tags where object_type='metacognitive_state' and object_key='persona_system_analyst'"
            ).fetchall()
            policy = conn.execute(
                "select enabled, description from recording_policy where trigger='mistake_discovered'"
            ).fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(discovery)
        self.assertEqual(discovery[0], 'Discovery')
        self.assertNotIn('external', discovery[1].lower())
        self.assertIn('data, code, or problems', discovery[1])
        self.assertIsNotNone(system_concept)
        self.assertEqual(system_concept[0], 'System')
        self.assertIsNotNone(influence_concept)
        self.assertEqual(influence_concept[0], 'Influence')
        self.assertIsNotNone(overlap)
        self.assertEqual(overlap[0], 'Overlap Reduction')
        self.assertIsNotNone(schema)
        self.assertEqual(schema[0], 'Schema Catalog')
        self.assertIsNotNone(canonical)
        self.assertEqual(canonical[0], 'Canonical home enforcement')
        self.assertGreaterEqual(len(links), 7)
        self.assertIn(('discovery', 'db_improvement_control_flow'), links)
        self.assertIn(('discovery', 'canonical_home_enforcement'), links)
        self.assertIn(('discovery', 'formal_analysis_workflow'), links)
        self.assertIn(('discovery', 'out_of_the_box_thinking'), links)
        self.assertTrue(any(r[0] == 'canonical_home_enforcement' and r[2] == 'overlap_reduction' for r in db_links))
        self.assertTrue(any(r[0] == 'canonical_home_enforcement' and r[2] == 'schema_catalog' for r in db_links))
        self.assertTrue(any(r[0] == 'system' and r[2] == 'system_recognition_heuristic' for r in db_links))
        self.assertTrue(any(r[0] == 'system' and r[2] == 'system_nesting_heuristic' for r in db_links))
        self.assertTrue(any(r[0] == 'system' and r[2] == 'thinking_engine_system_elements' for r in db_links))
        self.assertTrue(any(r[0] == 'schema_catalog' and r[2] == 'canonical_home_enforcement' for r in db_links))
        self.assertTrue(any(r[0] == 'schema_catalog' and r[2] == 'discovery' for r in db_links))
        self.assertTrue(any(r[0] == 'entrypoint' and r[2] == 'discovery' for r in db_links))
        self.assertTrue(any(r[0] == 'correction' and r[2] == 'overlap_reduction' for r in db_links))
        self.assertEqual(tag_rows, [('persona', 'Persona'), ('system', 'System'), ('trait', 'Trait')])
        self.assertGreaterEqual(persona_tagged, 1)
        self.assertGreaterEqual(system_tagged, 1)
        self.assertGreaterEqual(trait_tagged, 1)
        self.assertEqual(persona, ('Persona', 'Marks persona-mode metacognitive state entries.'))
        self.assertEqual(system, ('System', 'Marks system-level metacognitive state entries, including derived persona-to-system classification.'))
        self.assertEqual(trait, ('Trait', 'Marks reusable persona traits such as curiosity, caution, structure, and patience.'))
        self.assertGreaterEqual(persona_count, 1)
        self.assertTrue(any(r[0] == 'persona_system_analyst' and r[1] == 'persona' for r in persona_system_analyst_tags))
        self.assertEqual(system_concept_tagged, 1)
        self.assertEqual(influence_tagged, 3)
        self.assertEqual(policy, (1, 'Record when a mistake, omission, or missed link is discovered.'))

    def test_schema_catalog_can_find_views(self):
        conn = hardening.connect()
        try:
            row = conn.execute(
                "select object_name, object_type from v_schema_catalog where searchable_text like '%v_entry_points%' order by object_type, object_name limit 1"
            ).fetchone()
            entry_rows = conn.execute(
                "select object_name from v_schema_catalog where searchable_text like '%entry%' order by object_name limit 10"
            ).fetchall()
        finally:
            conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], 'v_entry_points')
        self.assertEqual(row[1], 'view')
        self.assertIn(('v_entry_points',), entry_rows)

    def test_component_influence_preset_view_is_present(self):
        conn = hardening.connect()
        try:
            rows = conn.execute(
                "select distinct mode_key from v_component_influence_presets order by mode_key"
            ).fetchall()
        finally:
            conn.close()

        self.assertIn(('default',), rows)
        self.assertIn(('evolved',), rows)
        self.assertIn(('error_recovery',), rows)

    def test_component_influence_modes_are_seeded(self):
        conn = hardening.connect()
        try:
            rows = conn.execute(
                "select mode_key from v_component_influence_modes order by mode_key"
            ).fetchall()
        finally:
            conn.close()

        self.assertEqual([r[0] for r in rows], ['default', 'error_recovery', 'evolved', 'high_attention', 'low_attention', 'startup'])

    def test_error_recovery_influence_preset_is_seeded(self):
        conn = hardening.connect()
        try:
            rows = conn.execute(
                "select component_key, mode_key, default_score, current_score from v_component_influence where mode_key='error_recovery' order by component_key"
            ).fetchall()
            evolved_rows = conn.execute(
                "select component_key, preset_score from v_component_influence_presets where mode_key='evolved' order by component_key"
            ).fetchall()
            default_rows = conn.execute(
                "select component_key, preset_score from v_component_influence_presets where mode_key='default' order by component_key"
            ).fetchall()
            default_current = conn.execute(
                "select component_key, mode_key, default_score, current_score from v_component_influence where mode_key='default' order by component_key"
            ).fetchall()
        finally:
            conn.close()

        keys = [r[0] for r in rows]
        self.assertGreaterEqual(len(rows), 5)
        self.assertIn('thinking_engine_recovery_component', keys)
        self.assertIn('correction', keys)
        self.assertIn('thinking_engine_uncertainty_component', keys)
        self.assertIn('thinking_engine_logging_component', keys)
        self.assertTrue(all(r[1] == 'error_recovery' for r in rows))
        self.assertTrue(all(r[3] >= r[2] for r in rows))
        evolved_keys = [r[0] for r in evolved_rows]
        self.assertGreaterEqual(len(evolved_rows), 10)
        self.assertIn('thinking_engine_learning_component', evolved_keys)
        self.assertIn('thinking_engine_representation_component', evolved_keys)
        self.assertIn('thinking_engine_retrieval_component', evolved_keys)
        self.assertIn('thinking_engine_workflow_component', evolved_keys)
        self.assertIn('thinking_engine_governance_component', evolved_keys)
        self.assertIn('system', evolved_keys)
        self.assertIn('influence', evolved_keys)
        self.assertEqual(default_rows, evolved_rows)
        self.assertEqual([(r[0], r[1], r[2], r[3]) for r in default_current], [(k, 'default', s, s) for k, s in default_rows])

    def test_component_influence_history_tracks_updates(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(hardening.DB_PATH, db_copy)
            conn = hardening.sqlite3.connect(db_copy)
            conn.execute('PRAGMA foreign_keys = ON')
            cur = conn.cursor()
            cur.execute("""
                insert into component_influence(component_type, component_key, mode_key, default_score, current_score, override_reason)
                values(?,?,?,?,?,?)
            """, ('concept', 'attention', 'default', 0.5, 0.5, 'initial preset'))
            cur.execute("update component_influence set current_score=?, override_reason=? where component_type=? and component_key=?", (0.7, 'more attention', 'concept', 'attention'))
            conn.commit()
            rows = cur.execute("select previous_score, current_score, delta from component_influence_history where component_type='concept' and component_key='attention' order by id").fetchall()
            conn.close()
        finally:
            shutil.rmtree(tmpdir)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], (0.5, 0.5, 0.0))
        self.assertEqual(rows[1], (0.5, 0.7, 0.19999999999999996))

    def test_tag_search_finds_persona_states(self):
        conn = hardening.connect()
        try:
            rows = conn.execute(
                "select object_key, object_title from v_tag_search where searchable_text like '%persona%' and object_type='metacognitive_state' order by object_key"
            ).fetchall()
        finally:
            conn.close()

        self.assertGreaterEqual(len(rows), 10)
        self.assertIn(('persona_builder', 'persona_builder'), rows)
        self.assertIn(('persona_moderator', 'persona_moderator'), rows)
        self.assertIn(('persona_system_analyst', 'persona_system_analyst'), rows)

    def test_quality_work_plans_are_linked(self):
        conn = hardening.connect()
        try:
            rows = conn.execute(
                "select object_key from concept_links where concept_key='quality' and object_type='work_plan' order by object_key"
            ).fetchall()
        finally:
            conn.close()

        self.assertEqual([r[0] for r in rows], [
            'core_thinking_patterns',
            'elegant_requirements_glossary',
            'high_quality_code_plan',
            'personal_ai_survival_plan',
            'seven_basic_tools_quality_integration',
            'super_sharp_thinking_engine',
        ])

    def test_tag_search_finds_system_concept(self):
        conn = hardening.connect()
        try:
            rows = conn.execute(
                "select object_key, object_title from v_tag_search where searchable_text like '%system%' and object_type='concept' order by object_key"
            ).fetchall()
        finally:
            conn.close()

        self.assertIn(('system', 'System'), rows)

    def test_influence_concept_and_modes_are_seeded(self):
        conn = hardening.connect()
        try:
            concept = conn.execute(
                "select name, description from concepts where concept_key='influence'"
            ).fetchone()
            tagged = conn.execute(
                "select count(*) from object_epistemic_tags where object_type='concept' and object_key='influence' and tag_key in ('epistemic:reasoning','epistemic:state','epistemic:constraint')"
            ).fetchone()[0]
            modes = conn.execute(
                "select count(*) from component_influence_modes"
            ).fetchone()[0]
        finally:
            conn.close()

        self.assertIsNotNone(concept)
        self.assertEqual(concept[0], 'Influence')
        self.assertEqual(tagged, 3)
        self.assertGreaterEqual(modes, 5)

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
                "select question, status, origin_reasoning_episode_id from v_open_question_flow where origin_reasoning_episode_id is not null and status='open' order by id limit 1"
            ).fetchone()
        finally:
            conn.close()

        self.assertGreaterEqual(seeded, expected)
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
