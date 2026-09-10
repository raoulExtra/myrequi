import json
import shutil
import tempfile
import unittest
from pathlib import Path

import mode_command
from input_action_router import InputActionRouter


class RouteModeCommandTests(unittest.TestCase):
    def _prepare_clean_copy(self, db_copy):
        mode_command.run_mode_command(['route', 'off'], db_path=db_copy)
        conn = mode_command.connect(db_copy)
        try:
            conn.execute("delete from feature_flag_events where feature_key='route_mode'")
            conn.execute("delete from journal where category='mode' and summary like 'Route recognition %'")
            conn.commit()
        finally:
            conn.close()

    def test_route_mode_on_off_status_updates_state_and_logs(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(mode_command.DB_PATH, db_copy)
            self._prepare_clean_copy(db_copy)

            result = json.loads(mode_command.run_mode_command(['route', 'on'], db_path=db_copy))
            self.assertEqual(result['feature_key'], 'route_mode')
            self.assertTrue(result['enabled'])
            self.assertEqual(result['active_route_mode'], 'routes')
            self.assertTrue(result['changed'])

            status = json.loads(mode_command.run_mode_command(['route', 'status'], db_path=db_copy))
            self.assertTrue(status['enabled'])
            self.assertEqual(status['active_route_mode'], 'routes')

            off = json.loads(mode_command.run_mode_command(['route', 'off'], db_path=db_copy))
            self.assertFalse(off['enabled'])
            self.assertEqual(off['active_route_mode'], 'general')

            conn = mode_command.connect(db_copy)
            try:
                flag = conn.execute("select enabled from feature_flags where feature_key='route_mode'").fetchone()[0]
                role = conn.execute("select value from metacognitive_state where state_key='active_route_mode'").fetchone()[0]
                events = conn.execute("select count(*) from feature_flag_events where feature_key='route_mode'").fetchone()[0]
            finally:
                conn.close()

            self.assertEqual(flag, 0)
            self.assertEqual(role, 'general')
            self.assertEqual(events, 2)
        finally:
            shutil.rmtree(tmpdir)

    def test_route_mode_gates_session_prompt_matching(self):
        tmpdir = Path(tempfile.mkdtemp())
        try:
            db_copy = tmpdir / 'continuity.db'
            shutil.copy2(mode_command.DB_PATH, db_copy)
            self._prepare_clean_copy(db_copy)

            router = InputActionRouter(db_copy)
            off_decision = router.match_input_to_route('session prompt hello there', 'text')
            self.assertIsNone(off_decision['route_name'])
            self.assertEqual(off_decision['action_type'], 'unknown')

            mode_command.run_mode_command(['route', 'on'], db_path=db_copy)
            router = InputActionRouter(db_copy)
            on_decision = router.match_input_to_route('session prompt hello there', 'text')
            self.assertEqual(on_decision['route_name'], 'session_prompt')
            self.assertEqual(on_decision['parameters']['group1'], 'hello there')
        finally:
            shutil.rmtree(tmpdir)


if __name__ == '__main__':
    unittest.main()
