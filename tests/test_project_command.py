import json
import shutil
import tempfile
import unittest
from pathlib import Path

import project_command


class ProjectCommandTests(unittest.TestCase):
    def test_mark_thinking_project_adds_project_object_link(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(project_command.DB_PATH, db_copy)
            conn = project_command.connect(db_copy)
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    insert into projects(
                        project_name, display_name, level_number, parent_project_id,
                        local_active, description, updated_by
                    ) values (?,?,?,?,?,?,?)
                    """,
                    ('thinking_demo_project', 'Thinking Demo Project', 1, None, 1, 'Project used for thinking-workspace tagging.', 'test'),
                )
                conn.commit()
            finally:
                conn.close()

            result = json.loads(project_command.run_project_command(['mark-thinking', 'thinking_demo_project'], db_path=db_copy))
            self.assertEqual(result['project_name'], 'thinking_demo_project')
            self.assertEqual(result['object_type'], 'concept')
            self.assertEqual(result['object_key'], 'thinking_project')
            self.assertEqual(result['relationship'], 'tracks')
            self.assertIn('thinking/project-reflection workspace', result['note'])
            self.assertTrue(result['changed'])

            conn = project_command.connect(db_copy)
            try:
                row = conn.execute(
                    """
                    select po.object_type, po.object_key, po.relationship, po.note
                    from project_objects po
                    join projects p on p.id = po.project_id
                    where p.project_name = ?
                    """,
                    ('thinking_demo_project',),
                ).fetchone()
            finally:
                conn.close()

            self.assertEqual(row, ('concept', 'thinking_project', 'tracks', 'This project is a thinking/project-reflection workspace'))
        finally:
            shutil.rmtree(tmpdir)

    def test_mark_thinking_project_is_idempotent(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(project_command.DB_PATH, db_copy)
            conn = project_command.connect(db_copy)
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    insert into projects(
                        project_name, display_name, level_number, parent_project_id,
                        local_active, description, updated_by
                    ) values (?,?,?,?,?,?,?)
                    """,
                    ('thinking_demo_project', 'Thinking Demo Project', 1, None, 1, 'Project used for thinking-workspace tagging.', 'test'),
                )
                conn.commit()
            finally:
                conn.close()

            project_command.mark_thinking_project('thinking_demo_project', db_path=db_copy)
            project_command.mark_thinking_project('thinking_demo_project', db_path=db_copy)

            conn = project_command.connect(db_copy)
            try:
                count = conn.execute(
                    """
                    select count(*)
                    from project_objects po
                    join projects p on p.id = po.project_id
                    where p.project_name = ?
                    """,
                    ('thinking_demo_project',),
                ).fetchone()[0]
            finally:
                conn.close()

            self.assertEqual(count, 1)
        finally:
            shutil.rmtree(tmpdir)


if __name__ == '__main__':
    unittest.main()
