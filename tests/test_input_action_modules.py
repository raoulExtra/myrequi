import unittest

from input_action_audit import importance_reason, preview_text
from input_action_matching import match_json_pattern, match_routing_rule
from input_action_output import extract_session_text, format_plain_result
from input_action_parsing import parse_input


class InputActionModuleTests(unittest.TestCase):
    def test_parse_input_preserves_structured_and_plain_text(self):
        self.assertEqual(parse_input('{"intent": "go"}', "json"), ({"intent": "go"}, '{"intent": "go"}'))
        self.assertEqual(parse_input("  go  ", "text"), (None, "go"))
        self.assertEqual(parse_input("{bad", "structured"), (None, "{bad"))

    def test_matching_helpers(self):
        self.assertEqual(
            match_json_pattern({"intent": "go"}, "$.intent", "json_path"),
            (True, {"$.intent": "go"}),
        )
        matched, extracted = match_routing_rule(
            {"pattern_type": "json_regex", "pattern_spec": r"^go\s+"},
            "go now",
            None,
        )
        self.assertTrue(matched)
        self.assertEqual(extracted["input_text"], "go now")

    def test_audit_and_output_helpers(self):
        self.assertEqual(preview_text({"status": "ok"}), '{"status": "ok"}')
        self.assertEqual(
            importance_reason({"route_name": "plan_start"}, True, {"status": "ok"}, None),
            "state_or_audit_route",
        )
        result = {"action_result": {"session_result": {"assistant_text": "hello"}}}
        self.assertEqual(format_plain_result(result), ["hello"])
        self.assertEqual(extract_session_text({"reply_text": "reply"}), "reply")


if __name__ == "__main__":
    unittest.main()
