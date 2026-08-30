import json
import shutil
import tempfile
import unittest
from pathlib import Path

import mode_command


class ScientistModeCommandTests(unittest.TestCase):
    def _prepare_clean_copy(self, db_copy):
        mode_command.run_mode_command(['scientist', 'off'], db_path=db_copy)
        conn = mode_command.connect(db_copy)
        try:
            conn.execute("delete from feature_flag_events where feature_key='scientist_mode'")
            conn.execute("delete from journal where category='mode' and summary like 'Scientist mode %'")
            conn.commit()
        finally:
            conn.close()

    def test_scientist_mode_on_updates_state_and_logs(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(mode_command.DB_PATH, db_copy)
            self._prepare_clean_copy(db_copy)

            result = json.loads(mode_command.run_mode_command(['scientist', 'on'], db_path=db_copy))
            self.assertEqual(result['feature_key'], 'scientist_mode')
            self.assertTrue(result['enabled'])
            self.assertEqual(result['active_role_mode'], 'scientist')
            self.assertTrue(result['changed'])

            conn = mode_command.connect(db_copy)
            try:
                flag = conn.execute("select enabled from feature_flags where feature_key='scientist_mode'").fetchone()[0]
                role = conn.execute("select value from metacognitive_state where state_key='active_role_mode'").fetchone()[0]
                events = conn.execute("select count(*) from feature_flag_events where feature_key='scientist_mode'").fetchone()[0]
                journal = conn.execute("select count(*) from journal where category='mode' and summary like 'Scientist mode enabled%'").fetchone()[0]
            finally:
                conn.close()

            self.assertEqual(flag, 1)
            self.assertEqual(role, 'scientist')
            self.assertEqual(events, 1)
            self.assertEqual(journal, 1)
        finally:
            shutil.rmtree(tmpdir)

    def test_scientist_mode_is_idempotent(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(mode_command.DB_PATH, db_copy)
            self._prepare_clean_copy(db_copy)

            mode_command.run_mode_command(['scientist', 'on'], db_path=db_copy)
            result = json.loads(mode_command.run_mode_command(['scientist', 'on'], db_path=db_copy))
            self.assertFalse(result['changed'])
            self.assertIn('already', result['message'].lower())

            conn = mode_command.connect(db_copy)
            try:
                events = conn.execute("select count(*) from feature_flag_events where feature_key='scientist_mode'").fetchone()[0]
            finally:
                conn.close()
            self.assertEqual(events, 1)
        finally:
            shutil.rmtree(tmpdir)

    def test_scientist_mode_off_resets_role_mode(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(mode_command.DB_PATH, db_copy)
            self._prepare_clean_copy(db_copy)

            mode_command.run_mode_command(['scientist', 'on'], db_path=db_copy)
            result = json.loads(mode_command.run_mode_command(['scientist', 'off'], db_path=db_copy))
            self.assertFalse(result['enabled'])
            self.assertEqual(result['active_role_mode'], 'general')

            conn = mode_command.connect(db_copy)
            try:
                flag = conn.execute("select enabled from feature_flags where feature_key='scientist_mode'").fetchone()[0]
                role = conn.execute("select value from metacognitive_state where state_key='active_role_mode'").fetchone()[0]
                events = conn.execute("select count(*) from feature_flag_events where feature_key='scientist_mode'").fetchone()[0]
            finally:
                conn.close()

            self.assertEqual(flag, 0)
            self.assertEqual(role, 'general')
            self.assertEqual(events, 2)
        finally:
            shutil.rmtree(tmpdir)


if __name__ == '__main__':
    unittest.main()
