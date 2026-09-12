import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scientist_command


class ScientistCommandTests(unittest.TestCase):
    def test_unwanted_content_overrides_trusted_domain(self):
        decision = scientist_command.classify_source(
            'https://www.nist.gov/research',
            'Official source',
            'This trusted page contains sexually explicit erotic content.',
        )
        self.assertFalse(decision['allowed'])
        self.assertEqual(decision['class'], 'blocked_unwanted_content')

    def test_source_policy_blocks_erotic_and_spam_content(self):
        self.assertEqual(
            scientist_command.detect_unwanted_content('This is sexually explicit erotic content.'),
            ['erotic'],
        )
        self.assertEqual(
            scientist_command.detect_unwanted_content('Click here now for free money.'),
            ['spam'],
        )
        self.assertFalse(scientist_command.classify_source(
            'https://www.nist.gov/research', 'Research', 'Peer-reviewed methods and results.'
        )['allowed'] is False)

    def test_source_policy_detects_attack_vector_content(self):
        vectors = scientist_command.detect_attack_vectors(
            'This page describes SQL injection, SSRF, path traversal, and ransomware.'
        )
        self.assertIn('sql_injection', vectors)
        self.assertIn('ssrf', vectors)
        self.assertIn('path_traversal', vectors)
        self.assertIn('malware', vectors)
        self.assertFalse(scientist_command.classify_source(
            'https://www.nist.gov/research', 'Research', 'The page contains a reverse shell payload.'
        )['allowed'])

    def test_source_policy_blocks_recognizable_advertising(self):
        self.assertTrue(scientist_command.is_recognizable_ad(
            'https://example.org/article?utm_source=ads', 'Article'
        ))
        self.assertTrue(scientist_command.is_recognizable_ad(
            'https://example.org/sponsored', 'Sponsored special offer'
        ))
        self.assertFalse(scientist_command.is_recognizable_ad(
            'https://www.nist.gov/research', 'Research article', 'Evidence and methods'
        ))

    def test_source_policy_allows_trusted_european_sources(self):
        for url in (
            'https://europa.eu/policies',
            'https://www.gov.uk/guidance',
            'https://www.bund.de/service',
            'https://www.esa.int/News',
        ):
            self.assertTrue(scientist_command.classify_source(url, 'Official source')['allowed'])
        self.assertEqual(
            scientist_command.classify_source('https://europa.eu/policies', 'Official source')['class'],
            'trusted_european',
        )

    def test_source_policy_blocks_chinese_and_hacker_sources(self):
        self.assertFalse(scientist_command.classify_source('https://example.cn/page', 'Example')['allowed'])
        self.assertFalse(scientist_command.classify_source('https://news.ycombinator.com/item?id=1', 'Discussion')['allowed'])
        allowed = scientist_command.filter_research_results([
            {'title': 'Allowed source', 'url': 'https://www.nist.gov/research'},
            {'title': 'Blocked source', 'url': 'https://example.cn/page'},
        ])
        self.assertEqual([item['title'] for item in allowed], ['Allowed source'])

    def test_scientist_analysis_route_and_requirement_present(self):
        conn = scientist_command.connect()
        try:
            route = conn.execute(
                "select command_template from command_routes where route_name='scientist_analyse'"
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
                    'url': 'https://www.nist.gov/paper-one',
                },
                {
                    'title': 'Paper Two',
                    'url': 'https://www.nist.gov/paper-two',
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
