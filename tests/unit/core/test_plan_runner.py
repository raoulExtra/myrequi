from pathlib import Path

from plans.runner import (
    PlanStep,
    compaction_confirmed,
    discover_numbered_plans,
    end_condition_met,
    rotate_active_logs,
    run_steps,
)


def test_run_steps_preserves_declaration_order_and_logs_comparable_evidence():
    events = []
    log = []

    result = run_steps(
        [
            PlanStep("first", lambda: events.append("first") or "one"),
            PlanStep("second", lambda: events.append("second") or "two"),
        ],
        approval_fn=lambda step: True,
        test_gate=lambda step: True,
        commit_gate=lambda step: True,
        log_fn=log.append,
    )

    assert events == ["first", "second"]
    assert [item.step for item in result.steps] == ["first", "second"]
    assert all(item.status == "GREEN" for item in result.steps)
    assert all(
        {"timestamp", "plan.step", "phase", "action", "command", "expected", "actual", "status"}
        <= set(line)
        for line in log
    )


def test_run_steps_stops_after_failure():
    events = []

    result = run_steps(
        [
            PlanStep("first", lambda: events.append("first")),
            PlanStep("second", lambda: events.append("second")),
        ],
        approval_fn=lambda step: True,
        test_gate=lambda step: step.name != "first",
        commit_gate=lambda step: True,
    )

    assert events == ["first"]
    assert result.completed is False
    assert result.steps[0].status == "FAILED"
    assert len(result.steps) == 1


def test_run_steps_rejects_unapproved_step_without_starting_it():
    started = []

    result = run_steps(
        [PlanStep("blocked", lambda: started.append(True))],
        approval_fn=lambda step: False,
    )

    assert started == []
    assert result.steps[0].status == "BLOCKED"
    assert result.completed is False


def test_runner_supports_log_rotation_end_condition_and_compaction_confirmation(tmp_path: Path):
    (tmp_path / "plan-execution.log").write_text("execution", encoding="utf-8")
    (tmp_path / "provider-error.log").write_text("provider", encoding="utf-8")

    archived = rotate_active_logs(tmp_path, timestamp="20260910T091742Z")

    assert [path.name for path in archived] == [
        "plan-execution-20260910T091742Z.log",
        "provider-error-20260910T091742Z.log",
    ]
    assert not (tmp_path / "plan-execution.log").exists()
    assert not (tmp_path / "provider-error.log").exists()
    assert end_condition_met([True, True])
    assert not end_condition_met([True, False])
    assert compaction_confirmed("Compaction completed.")
    assert not compaction_confirmed("cont")


def test_discover_numbered_plans_is_deterministic_and_ignores_other_files(tmp_path: Path):
    (tmp_path / "10-plan.md").write_text("ten", encoding="utf-8")
    (tmp_path / "2-plan.md").write_text("two", encoding="utf-8")
    (tmp_path / "notes.md").write_text("ignore", encoding="utf-8")
    (tmp_path / "done").mkdir()
    (tmp_path / "done" / "1-plan.md").write_text("ignore", encoding="utf-8")

    assert discover_numbered_plans(tmp_path) == [
        tmp_path / "2-plan.md",
        tmp_path / "10-plan.md",
    ]
