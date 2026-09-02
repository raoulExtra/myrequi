import json
import shutil
import tempfile
import unittest
from pathlib import Path

import memory_command


class MemoryCommandTests(unittest.TestCase):
    def test_memory_recall_route_and_requirement_present(self):
        conn = memory_command.connect()
        try:
            route = conn.execute(
                "select command_template from control_command_routes where route_name='memory_recall'"
            ).fetchone()
            requirement = conn.execute(
                "select requirement_key, title from continuity_requirements where requirement_key='CDB-01.3'"
            ).fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(route)
        self.assertIn('memory_command.py recall', route[0])
        self.assertEqual(requirement[0], 'CDB-01.3')
        self.assertIn('memory retrieval', requirement[1].lower())

    def test_memory_recall_ranks_matching_items(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(memory_command.DB_PATH, db_copy)
            conn = memory_command.connect(db_copy)
            try:
                cur = conn.cursor()
                cur.execute(
                    "insert into beliefs(slug,current_statement,confidence,status,current_version) values(?,?,?,?,?)",
                    ('retrieval_ultra_unique_memory_token_belief', 'ultra_unique_memory_token appears in this belief', 0.9, 'active', 1),
                )
                cur.execute(
                    "insert into journal(category,summary,status) values(?,?,?)",
                    ('retrieval_test_journal', 'This note also mentions ultra_unique_memory_token directly', 'active'),
                )
                conn.commit()
            finally:
                conn.close()

            result = json.loads(memory_command.run_memory_recall('ultra_unique_memory_token', db_path=db_copy))
            self.assertEqual(result['query'], 'ultra_unique_memory_token')
            self.assertGreaterEqual(result['hit_count'], 2)
            self.assertEqual(result['hits'][0]['source_type'], 'belief')
            self.assertEqual(result['hits'][0]['title'], 'retrieval_ultra_unique_memory_token_belief')
            sources = [hit['source_type'] for hit in result['hits']]
            self.assertIn('journal', sources)
        finally:
            shutil.rmtree(tmpdir)

    def test_memory_recall_can_filter_by_layer(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(memory_command.DB_PATH, db_copy)
            conn = memory_command.connect(db_copy)
            try:
                cur = conn.cursor()
                cur.execute(
                    "insert into beliefs(slug,current_statement,confidence,status,current_version) values(?,?,?,?,?)",
                    ('layer_filter_belief', 'layer_filter_token appears in this belief', 0.91, 'active', 1),
                )
                cur.execute(
                    "insert into journal(category,summary,status) values(?,?,?)",
                    ('layer_filter_journal', 'layer_filter_token also appears in this journal note', 'active'),
                )
                conn.commit()
            finally:
                conn.close()

            result = json.loads(memory_command.run_memory_recall('layer_filter_token', db_path=db_copy, layer='semantic'))
            self.assertEqual(result['layer'], 'semantic')
            self.assertGreaterEqual(result['hit_count'], 1)
            self.assertTrue(all(hit['memory_layer'] == 'semantic' for hit in result['hits']))
            sources = {hit['source_type'] for hit in result['hits']}
            self.assertIn('belief', sources)
            self.assertNotIn('journal', sources)
        finally:
            shutil.rmtree(tmpdir)

    def test_memory_recall_can_match_condition(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(memory_command.DB_PATH, db_copy)
            conn = memory_command.connect(db_copy)
            try:
                memory_command.ensure_support(conn)
                cur = conn.cursor()
                cur.execute(
                    "insert into beliefs(slug,current_statement,confidence,status,current_version) values(?,?,?,?,?)",
                    ('condition_recall_belief', 'This belief does not mention the probe token directly.', 0.88, 'active', 1),
                )
                cur.execute(
                    "insert or replace into memory_conditions(source_type, source_key, condition) values(?,?,?)",
                    ('belief', 'condition_recall_belief', 'recall_probe_condition_token'),
                )
                conn.commit()
            finally:
                conn.close()

            result = json.loads(memory_command.run_memory_recall('recall_probe_condition_token', db_path=db_copy, layer='semantic'))
            self.assertGreaterEqual(result['hit_count'], 1)
            hit = result['hits'][0]
            self.assertEqual(hit['source_type'], 'belief')
            self.assertEqual(hit['source_key'], 'condition_recall_belief')
            self.assertIn('recall_probe_condition_token', hit['condition'])
        finally:
            shutil.rmtree(tmpdir)

    def test_memory_recall_returns_belief_versions_for_old_text(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(memory_command.DB_PATH, db_copy)
            conn = memory_command.connect(db_copy)
            try:
                cur = conn.cursor()
                cur.execute(
                    "insert into beliefs(slug,current_statement,confidence,status,current_version) values(?,?,?,?,?)",
                    ('versioned_history_belief', 'alpha version token', 0.92, 'active', 1),
                )
                conn.commit()
                cur.execute(
                    "update beliefs set current_statement=?, current_version=? where slug=?",
                    ('beta version token', 2, 'versioned_history_belief'),
                )
                conn.commit()
            finally:
                conn.close()

            result = json.loads(memory_command.run_memory_recall('alpha version token', db_path=db_copy, layer='semantic'))
            self.assertGreaterEqual(result['hit_count'], 1)
            self.assertEqual(result['hits'][0]['source_type'], 'belief_version')
            self.assertEqual(result['hits'][0]['title'], 'versioned_history_belief')
            self.assertEqual(result['hits'][0]['version'], 1)
        finally:
            shutil.rmtree(tmpdir)

    def test_memory_recall_can_retrieve_provenance_parts(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(memory_command.DB_PATH, db_copy)
            conn = memory_command.connect(db_copy)
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    insert into beliefs(slug,current_statement,confidence,status,current_version)
                    values(?,?,?,?,?)
                    """,
                    (
                        'reasoning_episode_probe_belief',
                        'This reasoning episode probe stores uncertainty, reversibility, and provenance.',
                        0.93,
                        'active',
                        1,
                    ),
                )
                cur.execute(
                    """
                    insert into epistemic_receipts(
                        object_type, object_key, object_version, change_summary,
                        provenance_json, provenance_complete, confidence,
                        session_key, project_name, effect, previous_receipt_id, receipt_kind
                    ) values(?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        'belief',
                        'reasoning_episode_probe_belief',
                        '1',
                        'Belief created for reasoning episode provenance recall testing.',
                        '{"origin":"test","basis":"recall_provenance","detail":"reasoning episode uncertainty reversibility"}',
                        1,
                        1.0,
                        'test-session',
                        'continuity_db',
                        'new',
                        None,
                        'object',
                    ),
                )
                conn.commit()
            finally:
                conn.close()

            result = json.loads(memory_command.run_memory_recall('reasoning episode uncertainty reversibility', db_path=db_copy))
            self.assertGreaterEqual(result['hit_count'], 2)
            sources = {hit['source_type'] for hit in result['hits']}
            self.assertIn('belief', sources)
            self.assertIn('epistemic_receipt', sources)
            receipt_hit = next(hit for hit in result['hits'] if hit['source_type'] == 'epistemic_receipt')
            self.assertIn('provenance', receipt_hit['body'].lower())
            self.assertIn('reasoning episode uncertainty reversibility', receipt_hit['body'].lower())
        finally:
            shutil.rmtree(tmpdir)

    def test_memory_recall_reflects_trust_as_state_and_policy(self):
        trust_result = json.loads(memory_command.run_memory_recall('trust', db_path=memory_command.DB_PATH))
        trust_sources = {hit['source_type'] for hit in trust_result['hits']}
        self.assertIn('metacognitive_state', trust_sources)
        self.assertIn('belief', trust_sources)
        trust_hit = next(hit for hit in trust_result['hits'] if hit['source_type'] == 'metacognitive_state' and hit['source_key'] == 'trust')
        self.assertIn('reliability', trust_hit['body'].lower())

        policy_result = json.loads(memory_command.run_memory_recall('trust policy', db_path=memory_command.DB_PATH))
        policy_hit = next(hit for hit in policy_result['hits'] if hit['source_type'] == 'metacognitive_state' and hit['source_key'] == 'thinking_policy')
        self.assertIn('honesty', policy_hit['body'].lower())
        self.assertIn('trust', policy_hit['body'].lower())

    def test_memory_index_view_exists_and_contains_known_rows(self):
        conn = memory_command.connect()
        try:
            counts = dict(
                conn.execute(
                    "select source_type, count(*) from v_memory_index where source_type in ('belief','decision','metacognitive_state','concept','ethical_principle','tool_guide','synthesis','synthesis_conflict') group by source_type"
                ).fetchall()
            )
        finally:
            conn.close()

        self.assertGreater(counts.get('belief', 0), 0)
        self.assertGreater(counts.get('decision', 0), 0)
        self.assertGreater(counts.get('metacognitive_state', 0), 0)
        self.assertGreater(counts.get('concept', 0), 0)
        self.assertGreater(counts.get('ethical_principle', 0), 0)
        self.assertGreater(counts.get('tool_guide', 0), 0)
        self.assertGreater(counts.get('synthesis', 0), 0)
        self.assertGreater(counts.get('synthesis_conflict', 0), 0)


if __name__ == '__main__':
    unittest.main()
