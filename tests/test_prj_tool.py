import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'prj_tool.py'


class PrjToolTests(unittest.TestCase):
    def test_init_creates_project_folder_and_readme(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            result = subprocess.run(
                ['python3', str(SCRIPT), 'init', 'demo', '--base-dir', str(base)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue((base / 'demo').exists())
            self.assertTrue((base / 'demo' / 'README.md').exists())
            self.assertIn(str(base / 'demo'), result.stdout)

    def test_list_shows_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            proj = base / 'demo'
            (proj / 'docs').mkdir(parents=True)
            (proj / 'phase_0.md').write_text('phase0')
            (proj / 'docs' / 'note.txt').write_text('note')
            result = subprocess.run(
                ['python3', str(SCRIPT), 'list', 'demo', '--base-dir', str(base)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn('demo/', result.stdout)
            self.assertIn('phase_0.md', result.stdout)
            self.assertIn('docs/', result.stdout)

    def test_phases_lists_phase_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            proj = base / 'demo'
            proj.mkdir(parents=True)
            (proj / 'phase_0.md').write_text('phase0')
            (proj / 'phase_1.md').write_text('phase1')
            (proj / 'readme.md').write_text('ignore')
            result = subprocess.run(
                ['python3', str(SCRIPT), 'phases', 'demo', '--base-dir', str(base)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.stdout.split(), ['phase_0.md', 'phase_1.md'])

    def test_show_prints_phase_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            proj = base / 'demo'
            proj.mkdir(parents=True)
            (proj / 'phase_0.md').write_text('hello phase')
            result = subprocess.run(
                ['python3', str(SCRIPT), 'show', 'demo', '0', '--base-dir', str(base)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.stdout.strip(), 'hello phase')

    def test_parent_chain_reads_inherits_from_phase_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'base').mkdir(parents=True)
            (base / 'base' / 'phase_0.md').write_text('PROJECT PHASE 0\ninherits_from: -\n')
            (base / 'demo').mkdir(parents=True)
            (base / 'demo' / 'phase_0.md').write_text('PROJECT PHASE 0\ninherits_from: base\n')

            chain = __import__('prj_tool').parent_chain('demo', base_dir=base)
            self.assertEqual(chain, ['demo', 'base'])

    def test_parents_command_prints_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'base').mkdir(parents=True)
            (base / 'base' / 'phase_0.md').write_text('PROJECT PHASE 0\ninherits_from: -\n')
            (base / 'demo').mkdir(parents=True)
            (base / 'demo' / 'phase_0.md').write_text('PROJECT PHASE 0\ninherits_from: base\n')
            result = subprocess.run(
                ['python3', str(SCRIPT), 'parents', 'demo', '--base-dir', str(base)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.stdout.splitlines(), ['demo', 'base'])

    def test_create_recommended_subdirs_uses_highest_default_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'base').mkdir(parents=True)
            (base / 'base' / 'phase_0.md').write_text(
                'PROJECT PHASE 0\n'
                'inherits_from: -\n'
                'default_version: V00.00.01\n\n'
                'recommended_subdirs:\n'
                '- imple/<version>/\n'
                '- docs/ — overview, usage, project explanation\n'
            )
            (base / 'demo').mkdir(parents=True)
            (base / 'demo' / 'phase_0.md').write_text(
                'PROJECT PHASE 0\n'
                'inherits_from: base\n'
                'default_version: V00.00.02\n\n'
                'recommended_subdirs:\n'
                '- examples/ — sample outputs or mock content\n'
                '- imple/<version>/test/ — tests for that implementation version\n'
            )

            created = __import__('prj_tool').create_recommended_subdirs('demo', base_dir=base)
            self.assertEqual(created, ['docs/', 'examples/', 'imple/', 'imple/V00.00.02/', 'imple/V00.00.02/test/'])
            self.assertTrue((base / 'demo' / 'docs').is_dir())
            self.assertTrue((base / 'demo' / 'examples').is_dir())
            self.assertTrue((base / 'demo' / 'imple').is_dir())
            self.assertTrue((base / 'demo' / 'imple' / 'V00.00.02').is_dir())
            self.assertTrue((base / 'demo' / 'imple' / 'V00.00.02' / 'test').is_dir())

    def test_highest_default_version_walks_parent_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'base').mkdir(parents=True)
            (base / 'base' / 'phase_0.md').write_text('PROJECT PHASE 0\ninherits_from: -\ndefault_version: V00.00.01\n')
            (base / 'demo').mkdir(parents=True)
            (base / 'demo' / 'phase_0.md').write_text('PROJECT PHASE 0\ninherits_from: base\ndefault_version: V00.00.03\n')
            self.assertEqual(__import__('prj_tool').highest_default_version('demo', base_dir=base), 'V00.00.03')

    def test_subdirs_command_prints_created_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'base').mkdir(parents=True)
            (base / 'base' / 'phase_0.md').write_text(
                'PROJECT PHASE 0\n'
                'inherits_from: -\n'
                'default_version: V00.00.01\n\n'
                'recommended_subdirs:\n'
                '- docs/ — overview, usage, project explanation\n'
            )
            (base / 'demo').mkdir(parents=True)
            (base / 'demo' / 'phase_0.md').write_text(
                'PROJECT PHASE 0\n'
                'inherits_from: base\n'
                'default_version: V00.00.02\n\n'
                'recommended_subdirs:\n'
                '- examples/ — sample outputs or mock content\n'
                '- imple/<version>/test/ — tests for that implementation version\n'
            )
            result = subprocess.run(
                ['python3', str(SCRIPT), 'subdirs', 'demo', '--base-dir', str(base)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.stdout.splitlines(), ['docs/', 'examples/', 'imple/', 'imple/V00.00.02/', 'imple/V00.00.02/test/'])

    def test_subdirs_condition_on_tag_uses_current_project_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'base').mkdir(parents=True)
            (base / 'base' / 'phase_0.md').write_text(
                'PROJECT PHASE 0\n'
                'inherits_from: -\n'
                'default_version: V00.00.01\n\n'
                'recommended_subdirs:\n'
                'on tag: thinking_workspace\n'
                '- plans/ — work_plan templates and executions\n'
                '- docs/ — overview\n'
            )
            (base / 'demo').mkdir(parents=True)
            (base / 'demo' / 'phase_0.md').write_text(
                'PROJECT PHASE 0\n'
                'inherits_from: base\n'
                'default_version: V00.00.02\n\n'
                'tags:\n'
                '- thinking_workspace\n'
            )

            created = __import__('prj_tool').create_recommended_subdirs('demo', base_dir=base)
            self.assertIn('plans/', created)
            self.assertIn('docs/', created)
            self.assertTrue((base / 'demo' / 'plans').is_dir())
            self.assertTrue((base / 'demo' / 'docs').is_dir())

    def test_subdirs_condition_skips_without_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'base').mkdir(parents=True)
            (base / 'base' / 'phase_0.md').write_text(
                'PROJECT PHASE 0\n'
                'inherits_from: -\n'
                'default_version: V00.00.01\n\n'
                'recommended_subdirs:\n'
                'on tag: thinking_workspace\n'
                '- plans/ — work_plan templates and executions\n'
                '- docs/ — overview\n'
            )
            (base / 'demo').mkdir(parents=True)
            (base / 'demo' / 'phase_0.md').write_text(
                'PROJECT PHASE 0\n'
                'inherits_from: base\n'
                'default_version: V00.00.02\n'
            )

            created = __import__('prj_tool').create_recommended_subdirs('demo', base_dir=base)
            self.assertNotIn('plans/', created)
            self.assertIn('docs/', created)
            self.assertFalse((base / 'demo' / 'plans').exists())

    def test_project_tags_reads_chain_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'base').mkdir(parents=True)
            (base / 'base' / 'phase_0.md').write_text(
                'PROJECT PHASE 0\n'
                'inherits_from: -\n\n'
                'tags:\n'
                '- thinking_workspace\n'
                '- base_project\n'
            )
            (base / 'demo').mkdir(parents=True)
            (base / 'demo' / 'phase_0.md').write_text(
                'PROJECT PHASE 0\n'
                'inherits_from: base\n\n'
                'tags:\n'
                '- thinking_workspace\n'
                '- demo_project\n'
            )

            tags = __import__('prj_tool').project_tags_for('demo', base_dir=base)
            self.assertEqual(tags, ['thinking_workspace', 'demo_project', 'base_project'])

    def test_tags_command_prints_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'base').mkdir(parents=True)
            (base / 'base' / 'phase_0.md').write_text(
                'PROJECT PHASE 0\n'
                'inherits_from: -\n\n'
                'tags:\n'
                '- thinking_workspace\n'
            )
            (base / 'demo').mkdir(parents=True)
            (base / 'demo' / 'phase_0.md').write_text(
                'PROJECT PHASE 0\n'
                'inherits_from: base\n\n'
                'tags:\n'
                '- demo_project\n'
            )
            result = subprocess.run(
                ['python3', str(SCRIPT), 'tags', 'demo', '--base-dir', str(base)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.stdout.splitlines(), ['demo_project', 'thinking_workspace'])


if __name__ == '__main__':
    unittest.main()
