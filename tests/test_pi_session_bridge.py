import json
import unittest
from unittest.mock import patch

import pi_session
from input_action_router import InputActionRouter
from pathlib import Path
import sqlite3


class PiSessionBridgeTests(unittest.TestCase):
    @patch("pi_session.subprocess.check_output")
    def test_prompt_session_combines_state_and_send(self, mock_check_output):
        def fake_check_output(args, text=True):
            if "state" in args:
                return json.dumps({"type": "response", "data": {"session": "ready"}})
            if "send" in args:
                return json.dumps({"type": "response", "data": {"deliveredAs": "steer"}})
            raise AssertionError(f"unexpected args: {args}")

        mock_check_output.side_effect = fake_check_output

        result = pi_session.prompt_session("hello there", pid="42")

        self.assertEqual(result["prompt"], "hello there")
        self.assertEqual(result["pid"], "42")
        self.assertEqual(result["state"]["data"]["session"], "ready")
        self.assertEqual(result["send"]["data"]["deliveredAs"], "steer")

    def test_session_prompt_route_is_registered_and_matches(self):
        conn = sqlite3.connect("continuity.db")
        try:
            row = conn.execute(
                "select command_template from control_command_routes where route_name='session_prompt'"
            ).fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(row)
        self.assertIn("pi_session.py", row[0])

        router = InputActionRouter(Path("continuity.db"))
        decision = router.match_input_to_route("session prompt status please", "text")
        self.assertEqual(decision["route_name"], "session_prompt")
        self.assertEqual(decision["parameters"]["group1"], "status please")


if __name__ == "__main__":
    unittest.main()
