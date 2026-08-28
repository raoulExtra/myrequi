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
