import json
from pathlib import Path
import unittest

TOOL_PATH = Path('.pi/code-tools/fe_pending_instructs.py')


class BashStub:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, command):
        self.calls.append(command)
        if not self.responses:
            raise AssertionError(f'unexpected bash call: {command}')
        return self.responses.pop(0)


def load_tool(bash_stub):
    namespace = {'bash': bash_stub}
    exec(TOOL_PATH.read_text(), namespace)
    return namespace['fe_pending_instructs']


class FePendingInstructsTests(unittest.TestCase):
    def test_returns_empty_payload_when_fe_is_disabled(self):
        bash_stub = BashStub([json.dumps({'fe': False, 'pending': []})])
        tool = load_tool(bash_stub)

        result = json.loads(tool())

        self.assertEqual(result, {'fe': False, 'pending': []})
        self.assertEqual(len(bash_stub.calls), 1)

    def test_returns_pending_instruct_rows_in_order_when_fe_is_enabled(self):
        bash_stub = BashStub([
            json.dumps(
                {
                    'fe': True,
                    'pending': [
                        {'id': 2, 'content': 'Second instruction', 'status': 'pending'},
                        {'id': 7, 'content': 'Third instruction', 'status': 'pending'},
                    ],
                }
            )
        ])
        tool = load_tool(bash_stub)

        result = json.loads(tool())

        self.assertTrue(result['fe'])
        self.assertEqual([row['id'] for row in result['pending']], [2, 7])
        self.assertEqual([row['status'] for row in result['pending']], ['pending', 'pending'])

    def test_marks_processed_rows_done_after_execution_flow(self):
        bash_stub = BashStub([
            json.dumps(
                {
                    'fe': True,
                    'pending': [{'id': 1, 'content': 'Capital of Germany', 'status': 'pending'}],
                }
            )
        ])
        tool = load_tool(bash_stub)

        json.loads(tool())

        self.assertTrue(
            any("update instruct set status='done'" in call.lower() for call in bash_stub.calls),
            'expected pending instruct rows to be marked done after processing',
        )


if __name__ == '__main__':
    unittest.main()
