"""Deterministic, injectable execution primitives for numbered plans."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class PlanStep:
    name: str
    action: Callable[[], Any]


@dataclass
class StepResult:
    step: str
    status: str
    actual: str = ""
    error: str = ""


@dataclass
class RunResult:
    steps: list[StepResult] = field(default_factory=list)
    completed: bool = False


def _evidence(step: str, phase: str, action: str, command: str, expected: str, actual: str, status: str) -> dict[str, str]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "plan.step": step,
        "phase": phase,
        "action": action,
        "command": command,
        "expected": expected,
        "actual": actual,
        "status": status,
    }


def run_steps(
    steps: Iterable[PlanStep],
    *,
    approval_fn: Callable[[PlanStep], bool] | None = None,
    test_gate: Callable[[PlanStep], bool] | None = None,
    commit_gate: Callable[[PlanStep], bool] | None = None,
    log_fn: Callable[[dict[str, str]], None] | None = None,
) -> RunResult:
    """Execute steps in declaration order and stop at the first failed gate."""
    approve = approval_fn or (lambda step: True)
    test = test_gate or (lambda step: True)
    commit = commit_gate or (lambda step: True)
    emit = log_fn or (lambda evidence: None)
    result = RunResult()

    for step in steps:
        emit(_evidence(step.name, "WHAT_NEXT", "start", "", "step is ready", "", "PENDING"))
        if not approve(step):
            emit(_evidence(step.name, "APPROVAL", "check", "", "approved", "not approved", "BLOCKED"))
            result.steps.append(StepResult(step.name, "BLOCKED", error="step approval was not granted"))
            return result

        emit(_evidence(step.name, "RED", "test", "pytest", "failing test exists", "step started", "RED"))
        try:
            value = step.action()
            actual = "" if value is None else str(value)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            emit(_evidence(step.name, "IMPLEMENT", "execute", "", "step succeeds", error, "FAILED"))
            result.steps.append(StepResult(step.name, "FAILED", error=error))
            return result

        if not test(step):
            emit(_evidence(step.name, "GREEN", "pytest", "pytest", "tests pass", "test gate failed", "FAILED"))
            result.steps.append(StepResult(step.name, "FAILED", actual=actual, error="pytest gate failed"))
            return result
        emit(_evidence(step.name, "GREEN", "pytest", "pytest", "tests pass", "tests pass", "GREEN"))

        if not commit(step):
            emit(_evidence(step.name, "COMMIT", "git commit", "git commit", "commit succeeds", "commit gate failed", "FAILED"))
            result.steps.append(StepResult(step.name, "FAILED", actual=actual, error="commit gate failed"))
            return result
        emit(_evidence(step.name, "COMMIT", "git commit", "git commit", "commit succeeds", "commit succeeds", "GREEN"))
        result.steps.append(StepResult(step.name, "GREEN", actual=actual))

    result.completed = True
    return result


def rotate_active_logs(tmp_dir: Path, *, timestamp: str) -> list[Path]:
    """Move active execution/provider logs into ``tmp/done`` safely."""
    done_dir = tmp_dir / "done"
    done_dir.mkdir(parents=True, exist_ok=True)
    archived: list[Path] = []
    for name in ("plan-execution.log", "provider-error.log"):
        source = tmp_dir / name
        if not source.exists():
            continue
        stem = source.stem
        destination = done_dir / f"{stem}-{timestamp}.log"
        suffix = 1
        while destination.exists():
            destination = done_dir / f"{stem}-{timestamp}-{suffix}.log"
            suffix += 1
        source.rename(destination)
        archived.append(destination)
    return archived


def end_condition_met(checks: Iterable[bool]) -> bool:
    """Return true only when every user-defined completion check is true."""
    values = list(checks)
    return bool(values) and all(values)


def compaction_confirmed(message: str) -> bool:
    """Require the exact post-compaction confirmation before continuing."""
    return message == "Compaction completed."


def discover_numbered_plans(directory: Path) -> list[Path]:
    """Return direct ``N-plan.md`` files in numeric order."""
    found: list[tuple[int, Path]] = []
    for path in directory.iterdir():
        if not path.is_file():
            continue
        match = re.fullmatch(r"(\d+)-plan\.md", path.name)
        if match:
            found.append((int(match.group(1)), path))
    return [path for _, path in sorted(found, key=lambda item: (item[0], item[1].name))]
