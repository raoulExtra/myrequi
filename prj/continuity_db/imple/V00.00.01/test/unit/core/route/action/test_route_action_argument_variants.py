"""Route-action coverage across route types and argument forms."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from route.input_action_router import InputActionRouter
from route.input_action_execution import _telegram_action_response, _telegram_update_is_new

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path("prj/continuity_db/imple/V00.00.01/extension")))
from mocks import MockBridgeClient, mock_pi_session


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
    ("chat latest", "session_latest_answer", {}),
    ("chat trace", "chat_trace", {}),
    ("chat trace detail", "chat_trace_detail", {}),
    ("chat trace telegram", "chat_trace_telegram", {}),
    ("chat trace status", "chat_trace_status", {}),
    ("chat poller exists", "chat_poller_exists", {}),
    ("chat trace auto on", "chat_trace_auto", {"group1": "on"}),
    ("free_me", "free_me", {}),
    ("extension status", "extension_status", {}),
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

    def test_bash_log_is_removed_before_execution_and_delivered_afterward(self):
        log_path = self.tmpdir / "tmp" / "bash.log"
        log_path.parent.mkdir()
        log_path.write_text("stale")
        decision = self.router.match_input_to_route("b printf fresh > tmp/bash.log", "text")
        with patch(
            "message_adapter_registry.send_document_to_active_adapters",
            return_value=[{"adapter": "messenger-adapter.telegramm", "message_id": 8}],
        ) as send:
            result = self.router.execute_routing_decision(decision, "b printf fresh > tmp/bash.log")
        self.assertEqual(log_path.read_text(), "fresh")
        self.assertEqual(send.call_args.args[2], log_path)
        self.assertEqual(
            result["action_result"]["bash_log_delivery"],
            [{"adapter": "messenger-adapter.telegramm", "message_id": 8}],
        )

    def test_echo_returns_literal_output_without_shell_execution(self):
        decision = self.router.match_input_to_route("echo h", "text")
        result = self.router.execute_routing_decision(decision, "echo h")
        self.assertEqual(result["action_result"]["result"], "h")

    def test_detailed_action_log_is_not_written_when_debug_is_off(self):
        before = self.router.conn.execute("SELECT COUNT(*) FROM input_action_log").fetchone()[0]
        decision = self.router.match_input_to_route("echo debug-off", "text")
        self.router.execute_routing_decision(decision, "echo debug-off")
        after = self.router.conn.execute("SELECT COUNT(*) FROM input_action_log").fetchone()[0]
        self.assertEqual(after, before)

    def test_ordinary_x_prompt_does_not_trigger_recursion_denial(self):
        decision = self.router.match_input_to_route("still no send", "text")
        self.assertNotEqual(decision.get("route_name"), "telegram_poll")
        self.assertNotEqual(decision.get("route_name"), "telegram_receive_one")
        self.assertFalse((decision.get("recall_packet") or {}).get("recursion_blocked", False))

    def test_extension_status_lists_active_extensions_with_versions(self):
        decision = self.router.match_input_to_route("extension status", "text")
        result = self.router.execute_routing_decision(decision, "extension status")
        status = result["action_result"]
        self.assertEqual(status["status"], "extension_status")
        self.assertTrue(status["extensions"])
        for extension in status["extensions"]:
            self.assertIn("kind", extension)
            self.assertIn("type", extension)
            self.assertIn("version", extension)
            self.assertIn("tags", extension)
            self.assertTrue(extension["tags"])

    def test_free_me_disables_messenger_prefix(self):
        decision = self.router.match_input_to_route("free_me", "text")
        result = self.router.execute_routing_decision(decision, "free_me")
        self.assertEqual(result["action_result"]["status"], "messenger_prefix_disabled")
        enabled = self.router.conn.execute(
            "SELECT enabled FROM feature_flags WHERE feature_key='messenger_prefix_required'"
        ).fetchone()[0]
        self.assertEqual(enabled, 0)

    def test_chat_trace_auto_status_reports_enabled_state(self):
        decision = self.router.match_input_to_route("chat trace auto status", "text")
        result = self.router.execute_routing_decision(decision, "chat trace auto status")
        self.assertIn(result["action_result"]["result"], {"chat trace auto: on.", "chat trace auto: off."})

    def test_chat_poller_exists_sets_a_status_tag(self):
        decision = self.router.match_input_to_route("chat poller exists", "text")
        result = self.router.execute_routing_decision(decision, "chat poller exists")
        action = result["action_result"]
        self.assertEqual(action["status"], "chat_poller_exists")
        self.assertIn(action["tag_key"], {"status:chat_poller_present", "status:chat_poller_absent"})
        tag = self.router.conn.execute(
            "SELECT tag_key FROM object_epistemic_tags WHERE object_type='route' AND object_key='chat_poller_exists'"
        ).fetchone()[0]
        self.assertEqual(tag, action["tag_key"])

    def test_chat_trace_status_reports_delivery_modes(self):
        self.router.conn.execute("UPDATE feature_flags SET enabled=0 WHERE feature_key='chat_trace_auto'")
        self.router.conn.commit()
        decision = self.router.match_input_to_route("chat trace status", "text")
        result = self.router.execute_routing_decision(decision, "chat trace status")
        status = result["action_result"]
        self.assertEqual(status["status"], "chat_trace_status")
        self.assertIn("chat trace auto: off", status["result"])
        self.assertNotIn("route: available", status["result"])
        self.assertIn("active adapters: 1", status["result"])
        self.assertIn("telegram route: on", status["result"])

    def test_chat_trace_detail_returns_safe_tool_status(self):
        decision = self.router.match_input_to_route("chat trace detail", "text")
        with mock_pi_session():
            with patch(
                "pi_session.get_session_history",
                side_effect=[
                    {"data": {"events": [{"id": "start-1", "timestamp": "2026-09-12T10:00:00Z", "data": {"toolName": "bash"}}]}},
                    {"data": {"events": [{"id": "update-1", "timestamp": "2026-09-12T10:00:01Z", "data": {"toolName": "bash"}}]}},
                    {"data": {"events": [{"id": "end-1", "timestamp": "2026-09-12T10:00:02Z", "data": {"toolName": "bash", "status": "success"}}]}},
                ],
            ):
                result = self.router.execute_routing_decision(decision, "chat trace detail")
        action = result["action_result"]
        self.assertEqual(action["status"], "chat_trace_detail")
        self.assertIn("tool_execution_start: bash", action["result"])
        self.assertNotIn("args", action["result"])

    def test_chat_trace_returns_completed_chat_events(self):
        self.router.conn.execute(
            "UPDATE feature_flags SET enabled=0 WHERE feature_key='chat_trace_auto'"
        )
        self.router.conn.commit()
        decision = self.router.match_input_to_route("chat trace", "text")
        self.assertEqual(decision["route_name"], "chat_trace")
        with mock_pi_session():
            with patch(
                "pi_session.get_session_history",
                return_value={"data": {"events": [
                    {"id": "evt-1", "timestamp": "2026-09-12T10:00:00Z", "message": {"role": "user", "content": [{"type": "text", "text": "hello"}]}},
                    {"id": "evt-2", "timestamp": "2026-09-12T10:00:01Z", "message": {"role": "assistant", "content": [{"type": "text", "text": "hi <Peter>"}]}},
                ]}},
            ):
                result = self.router.execute_routing_decision(decision, "chat trace")
        action = result["action_result"]
        self.assertEqual(action["result"], "hi <Peter>")
        self.assertEqual(action["next_cursor"], "evt-2")
        self.assertEqual([event["role"] for event in action["events"]], ["user", "assistant"])

    def test_chat_trace_auto_delivers_standalone_trace(self):
        self.router.conn.execute(
            "UPDATE feature_flags SET enabled=1 WHERE feature_key='chat_trace_auto'"
        )
        self.router.conn.commit()
        decision = self.router.match_input_to_route("chat trace", "text")
        with mock_pi_session():
            with patch(
                "pi_session.get_session_history",
                return_value={"data": {"events": [
                    {"id": "evt-1", "message": {"role": "assistant", "content": [{"type": "text", "text": "trace output"}]}},
                ]}},
            ), patch(
                "message_adapter_registry.send_to_active_adapters",
                return_value=[{"adapter": "messenger-adapter.telegramm", "message_id": 7}],
            ) as send:
                result = self.router.execute_routing_decision(decision, "chat trace")
        self.assertEqual(send.call_args.args[2], "trace output")
        self.assertEqual(
            result["action_result"]["automatic_delivery"],
            [{"adapter": "messenger-adapter.telegramm", "message_id": 7}],
        )

    def test_duplicate_telegram_update_is_not_new(self):
        is_new, last_id = _telegram_update_is_new(42, None)
        self.assertTrue(is_new)
        self.assertEqual(last_id, 42)
        is_new, last_id = _telegram_update_is_new(42, last_id)
        self.assertFalse(is_new)
        self.assertEqual(last_id, 42)

    def test_older_telegram_update_is_not_new(self):
        is_new, last_id = _telegram_update_is_new(41, 42)
        self.assertFalse(is_new)
        self.assertEqual(last_id, 42)

    def test_one_input_executes_one_route_once(self):
        decision = self.router.match_input_to_route("echo h", "text")
        with patch.object(
            self.router,
            "execute_routing_decision",
            wraps=self.router.execute_routing_decision,
        ) as execute:
            result = self.router.execute_routing_decision(decision, "echo h")
        self.assertEqual(execute.call_count, 1)
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
