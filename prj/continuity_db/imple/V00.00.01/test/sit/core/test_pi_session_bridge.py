import json
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch

import mode_command
import pi_session
from route.input_action_router import InputActionRouter


class PiSessionBridgeTests(unittest.TestCase):
    @patch("pi_session.time.sleep", lambda *_: None)
    @patch("pi_session.datetime")
    @patch("pi_session.subprocess.check_output")
    def test_prompt_session_combines_state_send_and_history(self, mock_check_output, mock_datetime):
        calls = []
        mock_datetime.now.return_value = __import__('datetime').datetime(2026, 9, 8, 14, 0, 0, 123000, tzinfo=__import__('datetime').timezone.utc)

        def fake_check_output(args, text=True):
            calls.append(args)
            if "state" in args:
                return json.dumps({"type": "response", "data": {"pid": 42, "session": "ready"}})
            if "send" in args:
                return json.dumps({"type": "response", "command": "prompt", "success": True, "data": {"deliveredAs": "steer"}})
            if "history" in args:
                return json.dumps({"type": "response", "data": {"events": [{"timestamp": "2026-09-08T14:00:01.000Z", "event": "message_update", "data": {"message": {"role": "assistant", "content": [{"type": "text", "text": "Hello back."}]}}}]}})
            raise AssertionError(f"unexpected args: {args}")

        mock_check_output.side_effect = fake_check_output

        result = pi_session.prompt_session("hello there", pid="42")

        self.assertEqual(result["prompt"], "hello there")
        self.assertEqual(result["pid"], "42")
        self.assertEqual(result["state"]["data"]["session"], "ready")
        self.assertEqual(result["send"]["data"]["deliveredAs"], "steer")
        self.assertEqual(result["assistant_text"], "Hello back.")
        self.assertTrue(any("history" in call for call in calls))
        self.assertTrue(any("--since" in call for call in calls))

    @patch("pi_session.time.sleep", lambda *_: None)
    @patch("pi_session.datetime")
    @patch("pi_session.subprocess.check_output")
    def test_prompt_session_falls_back_to_broader_history(self, mock_check_output, mock_datetime):
        calls = []
        mock_datetime.now.return_value = __import__('datetime').datetime(2026, 9, 8, 14, 0, 0, 123000, tzinfo=__import__('datetime').timezone.utc)

        def fake_check_output(args, text=True):
            calls.append(args)
            if "state" in args:
                return json.dumps({"type": "response", "data": {"pid": 42, "session": "ready"}})
            if "send" in args:
                return json.dumps({"type": "response", "command": "prompt", "success": True, "data": {"deliveredAs": "now"}})
            if "history" in args and "--since" in args:
                return json.dumps({"type": "response", "data": {"events": []}})
            if "history" in args:
                return json.dumps({"type": "response", "data": {"events": [{"timestamp": "2026-09-08T14:00:02.000Z", "event": "message_update", "data": {"message": {"role": "assistant", "content": [{"type": "text", "text": "Fallback text."}]}}}]}})
            raise AssertionError(f"unexpected args: {args}")

        mock_check_output.side_effect = fake_check_output

        result = pi_session.prompt_session("hello there", pid="42")

        self.assertEqual(result["assistant_text"], "Fallback text.")
        self.assertGreaterEqual(sum(1 for call in calls if "history" in call), 2)

    @patch("pi_session.datetime")
    @patch("pi_session.subprocess.check_output")
    def test_latest_assistant_text_reads_history(self, mock_check_output, mock_datetime):
        mock_datetime.now.return_value = __import__('datetime').datetime(2026, 9, 8, 14, 0, 0, 123000, tzinfo=__import__('datetime').timezone.utc)

        def fake_check_output(args, text=True):
            if "history" in args:
                return json.dumps({"type": "response", "data": {"events": [{"timestamp": "2026-09-08T14:00:02.000Z", "event": "message_update", "data": {"message": {"role": "assistant", "content": [{"type": "text", "text": "I can list them."}]}}}]}})
            raise AssertionError(f"unexpected args: {args}")

        mock_check_output.side_effect = fake_check_output

        self.assertEqual(pi_session.latest_assistant_text(pid="42"), "I can list them.")

    @patch("pi_session.subprocess.check_output")
    def test_latest_assistant_text_skips_pending_thinking_and_uses_previous_answer(self, mock_check_output):
        def fake_check_output(args, text=True):
            if "history" in args:
                return json.dumps({"type": "response", "data": {"events": [
                    {"timestamp": "2026-09-08T15:11:54.474Z", "event": "message_update", "data": {"message": {"role": "assistant", "stopReason": "pending", "content": [{"type": "thinking", "thinking": "..."}, {"type": "toolCall", "name": "bash"}]}, "assistantMessageEvent": {"type": "toolcall_end", "partial": {"role": "assistant", "content": [{"type": "thinking", "thinking": "..."}, {"type": "toolCall", "name": "bash"}]}}}},
                    {"timestamp": "2026-09-08T15:10:00.000Z", "event": "message_update", "data": {"message": {"role": "assistant", "stopReason": "completed", "content": [{"type": "text", "text": "Africa has 54 sovereign nations."}]}}}
                ]}})
            raise AssertionError(f"unexpected args: {args}")

        mock_check_output.side_effect = fake_check_output

        self.assertEqual(pi_session.latest_assistant_text(pid="42"), "Africa has 54 sovereign nations.")

    @patch("pi_session.subprocess.check_output")
    def test_latest_assistant_text_joins_multiple_text_chunks(self, mock_check_output):
        def fake_check_output(args, text=True):
            if "history" in args:
                return json.dumps({"type": "response", "data": {"events": [
                    {"timestamp": "2026-09-08T15:10:00.000Z", "event": "message_update", "data": {"message": {"role": "assistant", "stopReason": "completed", "content": [
                        {"type": "text", "text": "Africa has 54 sovereign nations."},
                        {"type": "text", "text": "I can list them if you want."}
                    ]}}}
                ]}})
            raise AssertionError(f"unexpected args: {args}")

        mock_check_output.side_effect = fake_check_output

        self.assertEqual(pi_session.latest_assistant_text(pid="42"), "Africa has 54 sovereign nations.\nI can list them if you want.")

    @patch("pi_session.subprocess.Popen")
    def test_stream_session_observations_normalizes_events(self, mock_popen):
        lines = [
            json.dumps({"type": "session", "version": 3, "id": "abc", "timestamp": "2026-09-08T15:00:00.000Z", "cwd": "/tmp"}),
            json.dumps({"type": "message_update", "assistantMessageEvent": {"type": "text_delta", "contentIndex": 0, "delta": "Hello "}}),
            json.dumps({"type": "message_update", "assistantMessageEvent": {"type": "text_delta", "contentIndex": 0, "delta": "world"}}),
            json.dumps({"type": "auto_retry_start", "attempt": 1, "maxAttempts": 3, "delayMs": 2000, "errorMessage": "Overloaded"}),
            json.dumps({"type": "tool_execution_end", "toolCallId": "call_1", "toolName": "bash", "result": {"content": []}, "isError": True}),
            json.dumps({"type": "message_end", "message": {"role": "assistant", "content": [{"type": "text", "text": "Hello world"}], "stopReason": "stop"}}),
        ]

        mock_popen.return_value = type("P", (), {"stdout": lines})()

        observations = list(pi_session.stream_session_observations(pid="42"))
        kinds = [obs["kind"] for obs in observations]
        self.assertEqual(kinds[:3], ["session_header", "assistant_text_delta", "assistant_text_delta"])
        self.assertIn("retry_start", kinds)
        self.assertIn("tool_execution_end", kinds)
        self.assertEqual(observations[-1]["kind"], "assistant_message_end")
        self.assertEqual(observations[-1]["text"], "Hello world")
        self.assertEqual(observations[4]["decision_hint"], "tool_failed")

    def test_session_prompt_route_is_registered_and_matches(self):
        conn = sqlite3.connect("continuity.db")
        try:
            row = conn.execute(
                "select command_template from control_command_routes where route_name='session_prompt'"
            ).fetchone()
            latest_row = conn.execute(
                "select command_template from control_command_routes where route_name='session_latest_answer'"
            ).fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(row)
        self.assertIn("pi_session.py", row[0])
        self.assertIsNotNone(latest_row)
        self.assertIn("latest_assistant_text", latest_row[0])

        mode_command.run_mode_command(["route", "on"], db_path=Path("continuity.db"))
        try:
            router = InputActionRouter(Path("continuity.db"))
            decision = router.match_input_to_route("session prompt status please", "text")
            self.assertEqual(decision["route_name"], "session_prompt")
            self.assertEqual(decision["parameters"]["group1"], "status please")

            alias_decision = router.match_input_to_route("p status please", "text")
            self.assertEqual(alias_decision["route_name"], "session_prompt")
            self.assertEqual(alias_decision["parameters"]["group1"], "status please")

            latest_decision = router.match_input_to_route('pi_session.latest_assistant_text(pid="416965")', 'text')
            self.assertEqual(latest_decision["route_name"], "session_latest_answer")
            self.assertEqual(latest_decision["parameters"]["group1"], "416965")
        finally:
            mode_command.run_mode_command(["route", "off"], db_path=Path("continuity.db"))

    @patch("pi_session.latest_assistant_text", return_value="Africa has 54 sovereign nations.\nI can list them if you want.")
    def test_session_latest_answer_execution_returns_live_text(self, mock_latest):
        mode_command.run_mode_command(["route", "on"], db_path=Path("continuity.db"))
        try:
            router = InputActionRouter(Path("continuity.db"))
            decision = router.match_input_to_route('pi_session.latest_assistant_text(pid="416965")', 'text')
            result = router.execute_routing_decision(decision, 'pi_session.latest_assistant_text(pid="416965")', pid="416965")
            self.assertEqual(result["action_result"]["assistant_text"], "Africa has 54 sovereign nations.\nI can list them if you want.")
            self.assertEqual(result["action_result"]["pid"], "416965")
            mock_latest.assert_called_once_with(pid="416965")
        finally:
            mode_command.run_mode_command(["route", "off"], db_path=Path("continuity.db"))

    def test_plain_format_includes_session_text(self):
        router = InputActionRouter(Path("continuity.db"))
        result = {
            "action_result": {
                "command": "python3 pi_session.py hi",
                "session_result": {
                    "prompt": "hi",
                    "assistant_text": "Hello back.",
                },
            }
        }
        lines = router._format_plain_result(result)
        self.assertIn("Hello back.", "\n".join(lines))

    def test_session_prompt_action_result_exposes_assistant_text(self):
        router = InputActionRouter(Path("continuity.db"))
        result = {
            "action_result": {
                "command": "python3 pi_session.py hi",
                "assistant_text": "I can list them.",
                "session_result": {"assistant_text": "I can list them."},
            }
        }
        lines = router._format_plain_result(result)
        self.assertIn("I can list them.", "\n".join(lines))

    def test_session_model_set_route_is_registered_and_matches(self):
        conn = sqlite3.connect("continuity.db")
        try:
            row = conn.execute(
                "select command_template from control_command_routes where route_name='session_model_set'"
            ).fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(row)
        self.assertIn("set-model", row[0])
        self.assertIn("<provider>", row[0])

        mode_command.run_mode_command(["route", "on"], db_path=Path("continuity.db"))
        try:
            router = InputActionRouter(Path("continuity.db"))
            decision = router.match_input_to_route("/model:set gpt-5.4-mini", "text")
            self.assertEqual(decision["route_name"], "session_model_set")
            self.assertEqual(decision["parameters"]["group1"], "gpt-5.4-mini")
        finally:
            mode_command.run_mode_command(["route", "off"], db_path=Path("continuity.db"))

    @patch("route.input_action_router.time.sleep", lambda *_: None)
    def test_context_info_agent_tool_uses_bridge_when_available(self):
        router = InputActionRouter(Path("continuity.db"))
        decision = {"route_name": "context_info", "route_type": "agent_tool", "handler": "context_info"}

        responses = iter(
            [
                {"data": {"commands": [{"name": "context_info"}]}},
                {"data": {"deliveredAs": "now"}},
                {
                    "data": {
                        "events": [
                            {
                                "event": "tool_execution_end",
                                "data": {
                                    "toolName": "context_info",
                                    "result": {
                                        "content": [
                                            {"type": "text", "text": "Current context length: 7006 tokens (2.6% of maximum context window)."}
                                        ]
                                    },
                                },
                            }
                        ]
                    }
                },
            ]
        )

        with patch.object(router, "_select_bridge_pid", return_value=123), patch.object(
            router, "_bridge_request", side_effect=lambda *_args, **_kwargs: next(responses)
        ):
            result = router._execute_agent_tool(decision)

        self.assertEqual(result["handler"], "context_info")
        self.assertTrue(result["available"])
        self.assertEqual(result["pid"], 123)
        self.assertIn("7006 tokens", result["result"])


if __name__ == "__main__":
    unittest.main()
