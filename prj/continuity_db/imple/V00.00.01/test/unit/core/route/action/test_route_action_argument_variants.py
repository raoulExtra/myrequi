"""Route-action coverage across route types and argument forms."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from route.input_action_router import InputActionRouter
from route.input_action_execution import _telegram_action_response

sys.path.insert(0, str(Path(__file__).parent))
from mocks import MockBridgeClient


USE_MOCKS = os.getenv("ROUTE_ACTION_USE_MOCKS", "1").lower() not in {"0", "false", "no"}


ROUTE_ACTION_VARIANTS = (
    ("echo h", "echo_text", {"group1": "h"}),
    ("ethics on", "ethics_on", {}),
    ("ethics status", "ethics_status", {}),
    ("self-check", "self_check", {}),
    ("self check", "self_check", {}),
    ("continuity status", "self_check", {}),
    ("project on continuity_db", "project_on", {"group1": "continuity_db"}),
    ("project off demo", "project_off", {"group1": "demo"}),
    ("research SQLite testing", "research", {"group1": "SQLite testing"}),
    ("ctx", "context_info", {}),
    ("context info", "context_info", {}),
    ("usage percent", "context_info", {}),
    ("s telegram bot token", "telegram_bot_token", {}),
    ("tag assign tag routing epistemic:namespace", "tag_assign_safe", {
        "groups": ["tag", "routing", "epistemic:namespace"],
    }),
)


class RouteActionArgumentVariantTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.db_copy = self.tmpdir / "continuity.db"
        shutil.copy2(Path("continuity.db"), self.db_copy)
        self.router = InputActionRouter(self.db_copy, verbose=False)
        if USE_MOCKS:
            self.router._bridge_client = MockBridgeClient()

    def tearDown(self):
        self.router.stop()
        shutil.rmtree(self.tmpdir)

    def test_route_actions_match_each_argument_variant(self):
        for input_text, expected_route, expected_parameters in ROUTE_ACTION_VARIANTS:
            with self.subTest(input_text=input_text):
                decision = self.router.match_input_to_route(input_text, "text")
                self.assertEqual(decision["route_name"], expected_route)
                for key, value in expected_parameters.items():
                    self.assertEqual(decision["parameters"].get(key), value)

    def test_telegram_bash_response_returns_real_result(self):
        decision = self.router.match_input_to_route("b echo h", "text")
        result = self.router.execute_routing_decision(decision, "b echo h")
        self.assertEqual(_telegram_action_response(result, debug=False), "h")

    def test_bash_echo_returns_stdout(self):
        decision = self.router.match_input_to_route("b echo h", "text")
        result = self.router.execute_routing_decision(decision, "b echo h")
        self.assertEqual(result["action_result"]["stdout"], "h\n")
        self.assertEqual(result["action_result"]["result"], "h")

    def test_echo_returns_literal_output_without_shell_execution(self):
        decision = self.router.match_input_to_route("echo h", "text")
        result = self.router.execute_routing_decision(decision, "echo h")
        self.assertEqual(result["action_result"]["result"], "h")

    def test_context_info_action_uses_mock_or_real_bridge(self):
        decision = self.router.match_input_to_route("ctx", "text")
        result = self.router._execute_agent_tool(decision)
        self.assertEqual(result["handler"], "context_info")
        self.assertIn(result["status"], {"executed_agent", "unavailable"})
        if USE_MOCKS:
            self.assertTrue(result["available"])
            self.assertEqual(result["result"], "mock context info")

    def test_telegram_route_status_is_concise_when_debug_off(self):
        decision = self.router.match_input_to_route("route status", "text")
        result = self.router.execute_routing_decision(decision, "route status")
        response = _telegram_action_response(result, debug=False)
        self.assertIn("route mode", response.lower())
        self.assertNotIn("feature_key", response)
        self.assertNotIn("active_route_version", response)

    def test_telegram_route_status_response_value(self):
        decision = self.router.match_input_to_route("route status", "text")
        result = self.router.execute_routing_decision(decision, "route status")
        response = _telegram_action_response(result, debug=False)
        print(f"Telegram route status response: {response}")
        self.assertEqual(response, "route mode status")

    def test_telegram_token_action_calls_adapter(self):
        decision = self.router.match_input_to_route("s telegram bot token", "text")
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": ""}, clear=False):
            result = self.router._execute_agent_tool(decision)
        self.assertTrue(result["configured"])
        self.assertFalse(result["token_persisted"])
        if USE_MOCKS:
            self.assertEqual(self.router._bridge_client.telegram_bot.token, "mock-telegram-token")


if __name__ == "__main__":
    unittest.main()
