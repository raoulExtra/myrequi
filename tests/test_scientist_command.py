import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scientist_command


class ScientistCommandTests(unittest.TestCase):
    def test_scientist_analysis_route_and_requirement_present(self):
        conn = scientist_command.connect()
        try:
            route = conn.execute(
                "select command_template from control_command_routes where route_name='scientist_analyse'"
            ).fetchone()
            requirement = conn.execute(
                "select requirement_key, title from continuity_requirements where requirement_key in ('CDB-13.5','CDB-13.6') order by requirement_key"
            ).fetchall()
        finally:
            conn.close()

        self.assertIsNotNone(route)
        self.assertIn('scientist_command.py analyse', route[0])
        self.assertEqual([row[0] for row in requirement], ['CDB-13.5', 'CDB-13.6'])
        self.assertIn('Scientist analysis command', requirement[0][1])
        self.assertIn('Scientist web research', requirement[1][1])

    def test_topic_analysis_uses_live_web_research_and_creates_markdown_report(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(scientist_command.DB_PATH, db_copy)
            outdir = tmpdir / 'reports'

            fake_results = [
                {
                    'title': 'Paper One',
                    'url': 'https://example.com/paper-one',
                },
                {
                    'title': 'Paper Two',
                    'url': 'https://example.com/paper-two',
                },
            ]

            def fake_search(query, max_results=5):
                return fake_results[:max_results]

            def fake_fetch(url, timeout=20, max_chars=12000):
                if 'paper-one' in url:
                    return 'Paper one says the topic is important. It recommends cautious interpretation.'
                return 'Paper two reports stronger evidence and a clear method.'

            with patch.object(scientist_command, 'duckduckgo_search', side_effect=fake_search), patch.object(
                scientist_command, 'fetch_url_text', side_effect=fake_fetch
            ):
                result = json.loads(
                    scientist_command.run_scientist_analyse(
                        'mRNA vaccine safety evidence', db_path=db_copy, output_dir=outdir
                    )
                )

            report = Path(result['output_path'])
            self.assertTrue(report.exists())
            text = report.read_text(encoding='utf-8')
            self.assertIn('Scientist Analysis: mRNA vaccine safety evidence', text)
            self.assertIn('## Web research', text)
            self.assertIn('Paper One', text)
            self.assertIn('Paper Two', text)
            self.assertEqual(result['kind'], 'topic')
            self.assertIsNotNone(result['research_job_id'])

            conn = scientist_command.connect(db_copy)
            try:
                job = conn.execute(
                    'select status, query from research_jobs where id=?',
                    (result['research_job_id'],),
                ).fetchone()
                source_count = conn.execute(
                    'select count(*) from research_sources where job_id=?',
                    (result['research_job_id'],),
                ).fetchone()[0]
                journal_count = conn.execute(
                    "select count(*) from journal where category='scientist_analysis' and summary like 'Scientist analysis created for topic%'"
                ).fetchone()[0]
            finally:
                conn.close()

            self.assertEqual(job[0], 'completed')
            self.assertIn('mRNA vaccine safety evidence', job[1])
            self.assertEqual(source_count, 2)
            self.assertEqual(journal_count, 1)
        finally:
            shutil.rmtree(tmpdir)

    def test_file_analysis_creates_markdown_report(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(scientist_command.DB_PATH, db_copy)
            sample = tmpdir / 'sample_note.md'
            sample.write_text(
                '# Sample Note\n\n- First claim\n- Second claim\n\nSome explanatory text about the issue.\n',
                encoding='utf-8',
            )
            outdir = tmpdir / 'reports'

            result = json.loads(
                scientist_command.run_scientist_analyse(str(sample), db_path=db_copy, output_dir=outdir)
            )

            report = Path(result['output_path'])
            self.assertTrue(report.exists())
            text = report.read_text(encoding='utf-8')
            self.assertIn('Scientist Analysis: Sample Note', text)
            self.assertIn('First claim', text)
            self.assertIn('## Keywords', text)
            self.assertEqual(result['kind'], 'file')
            self.assertIsNone(result['research_job_id'])
        finally:
            shutil.rmtree(tmpdir)


if __name__ == '__main__':
    unittest.main()
