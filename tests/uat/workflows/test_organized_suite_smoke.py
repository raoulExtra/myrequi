"""Minimal UAT workflow proving the organized test/runtime boundary works."""


def test_organized_suite_exposes_plan_runner_and_optional_guard_boundary():
    from plans.runner import compaction_confirmed, discover_numbered_plans

    assert compaction_confirmed("Compaction completed.")
    assert callable(discover_numbered_plans)
