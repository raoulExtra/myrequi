import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'plans' / 'gen_plan.py'
DB = ROOT / 'continuity.db'


class GenPlanTests(unittest.TestCase):
    def test_prompt_mode_writes_single_markdown_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / 'plans'
            result = subprocess.run(
                ['python3', str(SCRIPT), '--db', str(DB), '--output-dir', str(outdir), '--prompt', 'Make a short plan for testing.'],
                check=True,
                capture_output=True,
                text=True,
            )
            files = sorted(outdir.glob('*_plan.md'))
            self.assertEqual(len(files), 1)
            text = files[0].read_text()
            self.assertIn('TODO[ ]', text)
            self.assertIn('Make a short plan for testing', text)
            self.assertIn('1_plan.md', result.stdout)

    def test_db_mode_includes_linked_plans(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / 'plans'
            subprocess.run(
                ['python3', str(SCRIPT), '--db', str(DB), '--output-dir', str(outdir), '--plan-key', 'next_action'],
                check=True,
                capture_output=True,
                text=True,
            )
            files = sorted(outdir.glob('*_plan.md'))
            # next_action has linked moderator_discussion in the DB.
            self.assertGreaterEqual(len(files), 2)
            combined = '\n'.join(f.read_text() for f in files)
            self.assertIn('Moderator-led discussion', combined)
            self.assertIn('TODO[ ]', combined)

    def test_only_marker_creates_numbered_steps(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / 'plans'
            subprocess.run(
                ['python3', str(SCRIPT), '--db', str(DB), '--output-dir', str(outdir), '--prompt', 'only: 1) output hello world 2) hi'],
                check=True,
                capture_output=True,
                text=True,
            )
            files = sorted(outdir.glob('*_plan.md'))
            self.assertEqual(len(files), 1)
            text = files[0].read_text()
            self.assertIn('1. TODO[ ] output hello world', text)
            self.assertIn('2. TODO[ ] hi', text)
            self.assertNotIn('## Name', text)
            self.assertNotIn('## Name', text)
            self.assertNotIn('## Objective', text)
            self.assertNotIn('## Notes', text)


if __name__ == '__main__':
    unittest.main()
