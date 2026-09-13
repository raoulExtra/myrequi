import io
import sqlite3
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from route.input_action_router import InputActionRouter


ROOT = Path(__file__).resolve().parents[7]


def isolated_router(tmp_path, pid="integration-session"):
    source = sqlite3.connect(f"file:{ROOT / 'continuity.db'}?mode=ro", uri=True)
    target_path = tmp_path / "continuity.db"
    target = sqlite3.connect(target_path)
    source.backup(target)
    target.close()
    source.close()
    return InputActionRouter(target_path, pid=pid, verbose=False)


def test_continuous_input_uses_clarification_gate(tmp_path):
    router = isolated_router(tmp_path)
    with patch("sys.stdin", io.StringIO("git add integration-file.txt?\n")):
        result = router.process_continuous_input()
    assert result["status"] == "clarification_required"
    assert result["question"] == "Which exact files or paths should be staged?"


def test_safe_route_execution_records_success(tmp_path):
    router = isolated_router(tmp_path)
    result = router.execute_routing_decision(router.match_input_to_route("echo integration"), "echo integration", pid="integration-session")
    assert result["success"] is True
    assert result["action_result"]["result"] == "integration"


def test_external_send_without_recipient_cannot_execute(tmp_path):
    router = isolated_router(tmp_path)
    before = router.conn.execute("SELECT COUNT(*) FROM route_execution_receipts").fetchone()[0]
    result = router.execute_routing_decision(router.match_input_to_route("send report.txt"), "send report.txt", pid="integration-session")
    after = router.conn.execute("SELECT COUNT(*) FROM route_execution_receipts").fetchone()[0]
    assert result["status"] == "clarification_required"
    assert result["risk_band"] == "very-high"
    assert after == before
