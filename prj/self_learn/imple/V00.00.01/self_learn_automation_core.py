from __future__ import annotations

import argparse
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import self_learn_meta as meta
from self_learn_named_docs import write_named_phase_0_doc, write_phase_0_core_requi_doc, write_phase_0_core_review_doc, write_named_phase_1_doc, write_phase_1_core_requi_doc, write_phase_1_core_review_doc
from self_learn_phase_2 import select_phase_2_mission, write_named_phase_2_doc, write_phase_2_core_requi_doc, write_phase_2_core_review_doc, write_phase_2
from self_learn_phase_docs import write_phase_requirements_doc, write_phase_challenge_doc, write_modularity_doc
from self_learn_phase_output import write_phase_0, write_phase_1
from self_learn_working_rules import write_working_rules_doc

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CANONICAL_DIRS = [
    "archive",
    "assets",
    "decisions",
    "docs",
    "examples",
    "imple/V00.00.01",
    "imple/V00.00.01/test",
    "plans",
    "plans/done",
    "references",
]

GLOSSARY_ROWS = [
    ("project", "A named workspace with its own filespace, goal, and operating rules.", "self_learn is the current project."),
    ("filespace", "The project directory tree that holds docs, plans, examples, and implementation.", "This is the working memory of the project."),
    ("phase", "A named stage of the project docs and workflow.", "phase_0.md is the entry point."),
    ("plan", "A bounded work unit with an objective and steps.", "Plans move to plans/done/ when complete."),
    ("step", "One actionable item inside a plan.", "Keep steps small and ordered."),
    ("goal", "The target state the project is trying to reach.", "Goals can drive plans and checkpoints."),
    ("outcome", "The result that actually happens after work.", "Outcomes are observed, not assumed."),
    ("objective", "The intended target or direction for a phase, plan, or project.", "Often broader than a goal and narrower than a mission; can contain multiple goals."),
    ("canonical", "The preferred default-facing term, file, or path.", "Use one canonical home per idea."),
    ("active", "Currently in progress.", "Active plans live outside plans/done/."),
    ("done", "Finished and retained for history.", "Completed plans move to plans/done/."),
    ("archive", "Superseded material kept for reference.", "Keep old material out of the active path."),
    ("refresh", "Sync the tree and rebuild generated views.", "Used by self_learn_automation.py."),
    ("checkpoint", "Refresh, stage, and commit the current filesystem state.", "This is the phase boundary action."),
    ("docs index", "A generated overview of docs, phases, and plans.", "Lives at docs/index.md."),
    ("learning loop", "Observe, update, verify, reuse.", "The core self-improvement cycle."),
    ("glossary", "The controlled vocabulary for the project.", "Add terms here before relying on them heavily."),
    ("future-proof", "Designed to remain usable as the project grows.", "Prefer stable terms, small definitions, and explicit aliases."),
    ("self_learn", "The project that improves its own filesystem and tools.", "This repo’s current self-improvement workspace."),
    ("continuity.db", "The durable database for project memory and state.", "Use it for persistent goals and checkpoints."),
    ("path", "An ordered route of work or learning steps.", "Used when AI suggests what to do next."),
    ("candidate", "One possible next path under consideration.", "Candidates are compared before selection."),
    ("suggestion", "An AI-proposed next path.", "Can be accepted, revised, or rejected."),
    ("recommendation", "A ranked suggestion with justification.", "More specific than a plain suggestion."),
    ("criteria", "The reasons one path is preferred over another.", "Should be explicit and reviewable."),
    ("priority", "The ranking weight that orders candidate paths.", "Higher priority wins unless criteria say otherwise."),
    ("feedback", "Observed results that change the next suggestion.", "Feeds the learning loop."),
    ("review", "A check of whether a path worked.", "Use after a path or plan."),
    ("requirement", "A defined condition that must be true.", "Requirements should be testable and explicit."),
    ("core requirement", "The small set of requirements that defines a phase.", "Every phase should have its own core requirements."),
    ("challenge", "A critical review that tries to break weak definitions.", "Use it to improve requirements before relying on them."),
    ("challenge prompt", "A question set given to AI for critique.", "Should ask for gaps, contradictions, and missing tests."),
    ("modularize", "Split a large file into smaller files or sections.", "Use when a file grows beyond the line budget."),
    ("line budget", "The maximum allowed line count for a file.", "Currently 700 lines."),
    ("oversized file", "A file that exceeds the line budget.", "Should trigger modularization before checkpointing."),
    ("next path", "The first or next learning route selected by AI.", "This is the phase-1 focus for self_learn."),
]

NEXT_PATH_ROWS = [
    ("path", "An ordered route from current state to a desired next state."),
    ("candidate", "One possible path that may become the next step."),
    ("suggestion", "An AI proposal for which path to take next."),
    ("recommendation", "A suggestion ranked with reasons and confidence."),
    ("criteria", "A rule or reason used to compare candidate paths."),
    ("priority", "A ranking signal that helps choose among candidates."),
    ("feedback", "Observed outcome data that changes the next suggestion."),
    ("review", "A check that evaluates whether the chosen path worked."),
]

MAX_FILE_LINES = 700
PHASE_REQUIREMENTS_MIN = 3

PHASE1_PLAN_KEY = "4_plan.md"
PHASE_REQUIREMENTS_PLAN_KEY = "5_plan.md"
PHASE_REVIEW_PLAN_KEY = "6_plan.md"
META_TRACE_PLAN_KEY = "7_plan.md"
PHASE1_PLAN_TITLE = "AI-first self-learn path"
PHASE1_PLAN_BODY = "Use the glossary and project state to suggest the first self-learn path, then verify and record the result."


@dataclass
class SyncReport:
    created_dirs: list[str]
    moved_plans: list[str]

    def as_dict(self) -> dict[str, list[str]]:
        return {"created_dirs": self.created_dirs, "moved_plans": self.moved_plans}
def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""
def _repo_root(root: Path) -> Path:
    root = root.resolve()
    if len(root.parents) >= 2:
        return root.parents[1]
    return root
def ensure_canonical_dirs(root: Path = PROJECT_ROOT) -> list[str]:
    created: list[str] = []
    root.mkdir(parents=True, exist_ok=True)
    for rel in CANONICAL_DIRS:
        path = root / rel
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path.relative_to(root)) + "/")
    return created
def move_completed_plans(root: Path = PROJECT_ROOT) -> list[str]:
    plans_dir = root / "plans"
    done_dir = plans_dir / "done"
    prep_dir = plans_dir / "prep"
    done_dir.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    for plan in sorted(plans_dir.glob("*_plan.md")):
        if plan.parent == done_dir:
            continue
        text = _read_text(plan).lower()
        if "status: completed" not in text and "status: done" not in text:
            continue
        target = done_dir / plan.name
        shutil.move(str(plan), str(target))
        moved.append(f"plans/done/{plan.name}")
    if prep_dir.exists():
        for plan in sorted(prep_dir.glob("*_plan.md")):
            text = _read_text(plan).lower()
            if "status: active" in text and "## when to run" in text:
                target = plans_dir / plan.name
                shutil.move(str(plan), str(target))
                moved.append(f"plans/{plan.name}")
    return moved
def sync(root: Path = PROJECT_ROOT) -> SyncReport:
    created_dirs = ensure_canonical_dirs(root)
    moved_plans = move_completed_plans(root)
    return SyncReport(created_dirs=created_dirs, moved_plans=moved_plans)
def _parse_phase_doc(path: Path) -> dict[str, object]:
    data: dict[str, object] = {"path": str(path), "goals": [], "core_requirements": []}
    section: str | None = None
    for raw_line in _read_text(path).splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "core_requirements:":
            section = "core_requirements"
            continue
        if stripped == "goals:":
            section = "goals"
            continue
        if section in {"core_requirements", "goals"} and stripped.startswith("- "):
            key = "core_requirements" if section == "core_requirements" else "goals"
            data[key].append(stripped[2:].strip())
            continue
        if section in {"core_requirements", "goals"} and not stripped.startswith("-") and ":" in stripped:
            section = None
        if ": " in stripped and not line.startswith(" "):
            key, value = stripped.split(": ", 1)
            data[key.strip()] = value.strip()
    data.setdefault("core_requirements", [])
    data.setdefault("goals", [])
    if not data.get("goal") and data.get("goals"):
        data["goal"] = data["goals"][0]
    return data

def phase_requirement_report(root: Path = PROJECT_ROOT) -> list[dict[str, object]]:
    report: list[dict[str, object]] = []
    for path in sorted(root.glob("phase_*.md")):
        data = _parse_phase_doc(path)
        requirements = list(data.get("core_requirements", []))
        phase_number = int(path.stem.split("_")[1]) if path.stem.startswith("phase_") and path.stem.split("_")[1].isdigit() else -1
        has_goals = bool(data.get("goals"))
        missing = []
        if phase_number == 0:
            missing.extend(field for field in ("purpose", "goal", "outcome", "status") if field not in data)
        else:
            if not has_goals:
                missing.append("goals")
            missing.extend(field for field in ("goal", "outcome", "status") if field not in data)
        if len(requirements) < PHASE_REQUIREMENTS_MIN:
            missing.append("core_requirements")
        report.append({
            "phase": path.name,
            "purpose": data.get("purpose"),
            "goal": data.get("goal"),
            "goals": data.get("goals", []),
            "outcome": data.get("outcome"),
            "outcome_doc": data.get("outcome_doc"),
            "status": data.get("status"),
            "core_requirements": requirements,
            "missing": missing,
        })
    return report
def enforce_phase_requirements(root: Path = PROJECT_ROOT) -> list[dict[str, object]]:
    report = phase_requirement_report(root)
    issues = [item for item in report if item["missing"]]
    if issues:
        summary = "; ".join(f"{item['phase']}: {', '.join(item['missing'])}" for item in issues)
        raise RuntimeError(f"Phase requirements must be defined and challenged before checkpointing: {summary}")
    return report
def phase_manifest(root: Path = PROJECT_ROOT) -> dict[str, object]:
    report = phase_requirement_report(root)
    return {
        "ready": all(not item["missing"] for item in report),
        "phase_count": len(report),
        "phases": report,
        "line_budget": MAX_FILE_LINES,
    }
def phase_challenge_bundle(root: Path = PROJECT_ROOT) -> dict[str, object]:
    return {"manifest": phase_manifest(root), "report": phase_requirement_report(root)}
def _count_text_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)
def modularity_budget(root: Path = PROJECT_ROOT, limit: int = MAX_FILE_LINES) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        try:
            line_count = _count_text_lines(path)
        except (OSError, UnicodeDecodeError):
            continue
        if line_count > limit:
            issues.append({
                "path": str(path.relative_to(root)),
                "line_count": line_count,
                "limit": limit,
                "over_by": line_count - limit,
            })
    return issues
def enforce_modularity_budget(root: Path = PROJECT_ROOT, limit: int = MAX_FILE_LINES) -> list[dict[str, object]]:
    issues = modularity_budget(root, limit)
    if issues:
        summary = ", ".join(f"{item['path']} ({item['line_count']} lines)" for item in issues)
        raise RuntimeError(f"Files over {limit} lines must be modularized first: {summary}")
    return issues
def _render_glossary() -> str:
    lines = [
        "# Glossary for self_learn",
        "",
        "This glossary is the shared vocabulary for the self_learn project.",
        "It is meant to stay small, clear, and extensible.",
        "",
        "## Canonical terms",
        "",
        "| Term | Meaning | Notes |",
        "| --- | --- | --- |",
    ]
    for term, meaning, notes in GLOSSARY_ROWS:
        lines.append(f"| {term} | {meaning} | {notes} |")
    lines.extend([
        "",
        "## Future-proofing rules",
        "",
        "1. Keep one canonical term per concept.",
        "2. Add aliases only when they reduce confusion.",
        "3. Prefer short definitions that still hold as the project grows.",
        "4. Separate target state (`goal`) from realized result (`outcome`).",
        "5. Separate active work (`plan`) from finished history (`done`).",
        "6. Update this glossary when a term becomes important enough to reuse.",
        "7. If a term starts to drift, add a note rather than rewriting history.",
    ])
    return "\n".join(lines) + "\n"
def write_glossary(root: Path = PROJECT_ROOT) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "glossary.md"
    path.write_text(_render_glossary(), encoding="utf-8")
    return path
def write_next_path_doc(root: Path = PROJECT_ROOT) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    content = [
        "# Next path",
        "",
        "This phase focuses on AI suggesting the first useful self-learn path.",
        "",
        "## terms",
        "",
        "| Term | Meaning |",
        "| --- | --- |",
    ]
    for term, meaning in NEXT_PATH_ROWS:
        content.append(f"| {term} | {meaning} |")
    content.extend([
        "",
        "## selection rules",
        "",
        "1. Prefer the highest-priority candidate that matches the glossary and current project state.",
        "2. Require explicit criteria for every ranked suggestion.",
        "3. Review the result before promoting the next path to a plan.",
        "4. Feed feedback back into the next suggestion.",
    ])
    path = docs_dir / "next-path.md"
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def write_readme(root: Path = PROJECT_ROOT) -> Path:
    path = root / "README.md"
    content = """# self_learn

Project entry point.

- [Project index](docs/index.md)
- [Glossary](docs/glossary.md)
- [Next path](docs/next-path.md)
- [Named phase 0 file](docs/phase-0-entry.md)
- [Phase 0 core requi file](docs/phase-0-core-requi.md)
- [Phase 0 core review](docs/phase-0-core-review.md)
- [Named phase 1 file](docs/phase-1-next-path.md)
- [Phase 1 core requi file](docs/phase-1-core-requi.md)
- [Phase 1 core review](docs/phase-1-core-review.md)
- [Phase requirements](docs/phase-requirements.md)
- [Phase challenge](docs/phase-challenge.md)
- [Modularity budget](docs/modularity.md)
- [Working rules](docs/working-rules.md)
- [Phase 0](phase_0.md)
- [Phase 1](phase_1.md)
- [Phase 2](phase_2.md)
- [Filesystem autonomy](docs/filesystem-autonomy.md)
- [Automation](docs/automation.md)
"""
    path.write_text(content, encoding="utf-8")
    return path
def write_next_phase_plan(root: Path = PROJECT_ROOT) -> Path:
    plans_dir = root / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    path = plans_dir / META_TRACE_PLAN_KEY
    content = f"""# Self-learn meta optimization plan

status: active

## objective
Automate the trace of self-learning optimization so the project can see its own improvement signals.

## steps
1. Generate a meta optimization trace from phase state and modularity signals.
2. Persist the trace in docs and continuity.db.
3. Use the trace to guide the next self-learning review.
4. Keep the trace format small and durable.
"""
    path.write_text(content, encoding="utf-8")
    return path
def _active_plan_paths(root: Path = PROJECT_ROOT) -> list[Path]:
    plans_dir = root / "plans"
    done_dir = plans_dir / "done"
    active: list[Path] = []
    for plan in sorted(plans_dir.glob("*_plan.md")):
        if plan.parent == done_dir:
            continue
        if "status: active" in _read_text(plan).lower():
            active.append(plan)
    return active
def _extract_plan_title_and_objective(plan: Path) -> tuple[str, str, list[str], list[str]]:
    title = plan.stem
    objective = ""
    steps: list[str] = []
    when_to_run: list[str] = []
    section: str | None = None
    for raw_line in _read_text(plan).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("# ") and title == plan.stem:
            title = line[2:].strip()
            continue
        if line == "## objective":
            section = "objective"
            continue
        if line == "## when to run":
            section = "when_to_run"
            continue
        if line == "## steps":
            section = "steps"
            continue
        if line.startswith("## "):
            section = None
            continue
        if section == "objective" and not objective:
            objective = line
        elif section == "when_to_run" and line.startswith("-"):
            when_to_run.append(line[1:].strip())
        elif section == "steps" and line[0].isdigit() and ". " in line:
            steps.append(line)
    return title, objective, when_to_run, steps
def _plan_is_phase_related(plan: Path) -> bool:
    text = _read_text(plan).lower()
    return "phase" in plan.name.lower() or "phase" in text
def write_active_plan_handoff(root: Path = PROJECT_ROOT) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "active-plan.md"
    active_plans = _active_plan_paths(root)
    lines = [
        "# Active plan handoff",
        "This file is generated when the project has an active plan.",
        "It tells the next AI run what to do and where to store the result.",
    ]
    if not active_plans:
        lines.extend([
            "## active plans",
            "- none",
            "## rule",
            "- If a plan appears, run it before creating the next checkpoint.",
            "- Store the outcome in a dedicated execution record under `plans/done/`.",
        ])
    else:
        lines.extend(["## active plans"])
        for plan in active_plans:
            title, objective, when_to_run, steps = _extract_plan_title_and_objective(plan)
            lines.append(f"### {plan.name}")
            lines.append(f"- title: {title}")
            lines.append(f"- source: {plan.relative_to(root)}")
            if _plan_is_phase_related(plan):
                if objective:
                    lines.append(f"- purpose: {objective}")
            elif objective:
                lines.append(f"- objective: {objective}")
            if when_to_run:
                lines.append("- when to run:")
                lines.extend(f"  - {item}" for item in when_to_run)
            if steps:
                lines.append("- steps:")
                lines.extend(f"  - {step}" for step in steps)
            lines.extend([
                f"- outcome store: plans/done/{plan.stem}_exec_<timestamp>.md",
                "- completion rule: update the source plan to status: completed, then let sync move it into plans/done/.",
                "",
            ])
        lines.extend([
            "## rule",
            "- Run the active plan before creating the next checkpoint.",
            "- Store the outcome in a dedicated execution record under `plans/done/`.",
            "- Keep the execution record readable and small.",
        ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
def write_plan_execution_record(root: Path, plan: Path, summary: str, details: list[str]) -> Path:
    done_dir = root / "plans" / "done"
    done_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    path = done_dir / f"{plan.stem}_exec_{stamp}.md"
    title, objective, when_to_run, steps = _extract_plan_title_and_objective(plan)
    lines = [
        f"# {title} — execution record",
        "",
        "## source",
        f"- plan: `{plan.relative_to(root)}`",
        f"- title: {title}",
    ]
    if _plan_is_phase_related(plan):
        if objective:
            lines.append(f"- purpose: {objective}")
    elif objective:
        lines.append(f"- objective: {objective}")
    if when_to_run:
        lines.append("- when to run:")
        lines.extend(f"  - {item}" for item in when_to_run)
    if steps:
        lines.append("- steps:")
        lines.extend(f"  - {step}" for step in steps)
    lines.extend(["", "## outcome", summary or "- none recorded", "", "## details"])
    lines.extend(details or ["- none recorded"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
def docs_index(root: Path = PROJECT_ROOT) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    plans_dir = root / "plans"
    done_dir = plans_dir / "done"
    active_plans = sorted(p.name for p in plans_dir.glob("*_plan.md") if p.parent != done_dir)
    done_plans = sorted(p.name for p in done_dir.glob("*_plan.md")) if done_dir.exists() else []
    docs = sorted(p.name for p in docs_dir.glob("*.md") if p.name != "index.md")
    phases = sorted(p.name for p in root.glob("phase_*.md"))
    content = [
        "# self_learn index",
        "",
        "## phases",
    ]
    content.extend(f"- [{name}](../{name})" for name in phases)
    content.extend(["", "## docs"])
    content.extend(f"- [{name}](./{name})" for name in docs)
    content.extend(["", "## active plans"])
    content.extend(f"- [{name}](../plans/{name})" for name in active_plans)
    content.extend(["", "## done plans"])
    content.extend(f"- [{name}](../plans/done/{name})" for name in done_plans)
    content.extend(["", "## canonical dirs"])
    content.extend(f"- {rel}/" for rel in CANONICAL_DIRS)
    content.extend(["", "## refresh", "Run `python3 imple/V00.00.01/self_learn_automation.py refresh --root .` to resync the tree."])
    path = docs_dir / "index.md"
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path
def status(root: Path = PROJECT_ROOT) -> dict[str, object]:
    plans_dir = root / "plans"
    done_dir = plans_dir / "done"
    active_plans = sorted(p.name for p in plans_dir.glob("*_plan.md") if p.parent != done_dir)
    done_plans = sorted(p.name for p in done_dir.glob("*_plan.md")) if done_dir.exists() else []
    phase_report = phase_requirement_report(root)
    modularity = modularity_budget(root)
    snapshot = {
        "root": str(root),
        "dirs": [str((root / rel).relative_to(root)) + "/" for rel in CANONICAL_DIRS if (root / rel).exists()],
        "phases": sorted(p.name for p in root.glob("phase_*.md")),
        "active_plans": active_plans,
        "done_plans": done_plans,
        "docs": sorted(p.name for p in (root / "docs").glob("*.md")) if (root / "docs").exists() else [],
        "docs_index": str(root / "docs" / "index.md") if (root / "docs" / "index.md").exists() else None,
    }
    return {
        **snapshot,
        "modularity_budget": modularity,
        "phase_requirements_report": phase_report,
        "meta_trace": meta.build_meta_trace(root, phase_report, modularity, snapshot),
    }
def refresh(root: Path = PROJECT_ROOT) -> dict[str, object]:
    report = sync(root)
    base_phase_report = phase_requirement_report(root)
    phase_2_doc = write_phase_2(root, base_phase_report)
    phase_report = phase_requirement_report(root)
    phase_2_doc = write_phase_2(root, phase_report)
    phase_report = phase_requirement_report(root)
    modularity = modularity_budget(root)
    snapshot = status(root)
    meta_trace = meta.build_meta_trace(root, phase_report, modularity, snapshot)
    meta_files = meta.write_meta_trace_files(root, meta_trace)
    meta_state = meta.update_meta_trace_state(root, meta_trace)
    glossary_path = write_glossary(root)
    next_path_doc = write_next_path_doc(root)
    phase_0_doc = write_phase_0(root)
    phase_1_doc = write_phase_1(root)
    phase_2_doc = write_phase_2(root, base_phase_report)
    readme = write_readme(root)
    named_phase_0_doc = write_named_phase_0_doc(root)
    phase_0_core_requi_doc = write_phase_0_core_requi_doc(root)
    phase_0_core_review_doc = write_phase_0_core_review_doc(root)
    named_phase_1_doc = write_named_phase_1_doc(root)
    phase_1_core_requi_doc = write_phase_1_core_requi_doc(root)
    phase_1_core_review_doc = write_phase_1_core_review_doc(root)
    phase_2_packet = select_phase_2_mission(base_phase_report)
    named_phase_2_doc = write_named_phase_2_doc(root, base_phase_report)
    phase_2_core_requi_doc = write_phase_2_core_requi_doc(root, base_phase_report)
    phase_2_core_review_doc = write_phase_2_core_review_doc(root, base_phase_report)
    phase_report = phase_requirement_report(root)
    modularity = modularity_budget(root)
    snapshot = status(root)
    meta_trace = meta.build_meta_trace(root, phase_report, modularity, snapshot)
    meta_files = meta.write_meta_trace_files(root, meta_trace)
    meta_state = meta.update_meta_trace_state(root, meta_trace)
    requirements_doc = write_phase_requirements_doc(root, phase_report)
    challenge_doc = write_phase_challenge_doc(root, phase_report)
    active_plan_handoff = write_active_plan_handoff(root)
    modularity_doc = write_modularity_doc(root, MAX_FILE_LINES)
    working_rules_doc = write_working_rules_doc(root)
    index_path = docs_index(root)
    return {
        **report.as_dict(),
        "glossary": str(glossary_path),
        "next_path": str(next_path_doc),
        "named_phase_0": str(named_phase_0_doc),
        "phase_0_core_requi": str(phase_0_core_requi_doc),
        "phase_0_core_review": str(phase_0_core_review_doc),
        "phase_0": str(phase_0_doc),
        "phase_1": str(phase_1_doc),
        "phase_2": str(phase_2_doc),
        "readme": str(readme),
        "named_phase_1": str(named_phase_1_doc),
        "phase_1_core_requi": str(phase_1_core_requi_doc),
        "phase_1_core_review": str(phase_1_core_review_doc),
        "named_phase_2": str(named_phase_2_doc),
        "phase_2_core_requi": str(phase_2_core_requi_doc),
        "phase_2_core_review": str(phase_2_core_review_doc),
        "phase_2_learning_path": phase_2_packet,
        "phase_requirements": str(requirements_doc),
        "phase_challenge": str(challenge_doc),
        "active_plan_handoff": str(active_plan_handoff),
        "modularity": str(modularity_doc),
        "working_rules": str(working_rules_doc),
        "docs_index": str(index_path),
        "modularity_budget": modularity,
        "phase_requirements_report": phase_report,
        "phase_manifest": phase_manifest(root),
        "phase_challenge_bundle": phase_challenge_bundle(root),
        "meta_trace": meta_trace,
        **meta_files,
        "meta_state": meta_state,
    }
def advance(root: Path = PROJECT_ROOT) -> dict[str, object]:
    for plan_name in ("3_plan.md", "6_plan.md"):
        plan = root / "plans" / plan_name
        if plan.exists():
            text_content = _read_text(plan)
            if "status: completed" not in text_content.lower():
                if "status: active" in text_content:
                    text_content = text_content.replace("status: active", "status: completed", 1)
                else:
                    text_content = text_content.replace("## objective", "status: completed\n\n## objective", 1)
                plan.write_text(text_content, encoding="utf-8")
    phase_0 = write_phase_0(root)
    phase_1 = write_phase_1(root)
    readme = write_readme(root)
    next_plan = write_next_phase_plan(root)
    report = refresh(root)
    docs_index(root)
    update_project_goal(root)
    git_report = git_checkpoint(root, message="self_learn: advance to phase 1")
    return {
        **report,
        "phase_0": str(phase_0),
        "phase_1": str(phase_1),
        "readme": str(readme),
        "next_plan": str(next_plan),
        "git": git_report,
    }
def update_project_goal(root: Path = PROJECT_ROOT) -> None:
    repo_root = _repo_root(root)
    db_path = repo_root / "continuity.db"
    if not db_path.exists():
        return
    goal = "Use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, suggest the first self-learn path, and modularize files over 700 lines."
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "update metacognitive_state set value=?, version=?, updated_at=CURRENT_TIMESTAMP where state_key='project_goal__self_learn'",
            (goal, 5),
        )
        conn.commit()
    finally:
        conn.close()
def git_checkpoint(root: Path = PROJECT_ROOT, message: str = "self_learn: filesystem checkpoint") -> dict[str, object]:
    phase_report = enforce_phase_requirements(root)
    issues = enforce_modularity_budget(root)
    repo_root = _repo_root(root)
    rel_root = str(root.resolve().relative_to(repo_root))
    subprocess.run(["git", "-C", str(repo_root), "add", rel_root, "continuity.db"], check=True)
    diff = subprocess.run(["git", "-C", str(repo_root), "diff", "--cached", "--quiet"])
    if diff.returncode == 0:
        return {"repo_root": str(repo_root), "staged": [], "committed": False, "message": message, "modularity_budget": issues, "phase_requirements_report": phase_report}
    subprocess.run(["git", "-C", str(repo_root), "commit", "-m", message], check=True)
    rev = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"], check=True, capture_output=True, text=True)
    return {"repo_root": str(repo_root), "staged": [rel_root, "continuity.db"], "committed": True, "message": message, "commit": rev.stdout.strip(), "modularity_budget": issues, "phase_requirements_report": phase_report}
def checkpoint(root: Path = PROJECT_ROOT, message: str = "self_learn: filesystem checkpoint") -> dict[str, object]:
    report = advance(root)
    return {**report, "git": report["git"], "checkpoint": message}
def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Self-learn filesystem automation helper")
    parser.add_argument("action", choices=["sync", "refresh", "advance", "checkpoint", "status", "budget", "challenge", "review"])
    parser.add_argument("--root", default=str(PROJECT_ROOT), help="Project root directory")
    args = parser.parse_args(list(argv) if argv is not None else None)
    root = Path(args.root)

    if args.action == "sync":
        print(sync(root).as_dict())
        return 0
    if args.action == "refresh":
        print(refresh(root))
        return 0
    if args.action == "advance":
        print(advance(root))
        return 0
    if args.action == "checkpoint":
        print(checkpoint(root))
        return 0
    if args.action == "status":
        print(status(root))
        return 0
    if args.action == "budget":
        print({"limit": MAX_FILE_LINES, "modularity_budget": modularity_budget(root)})
        return 0
    if args.action == "challenge":
        phase_report = phase_requirement_report(root)
        print({"phase_manifest": phase_manifest(root), "phase_challenge_bundle": phase_challenge_bundle(root), "phase_challenge": str(write_phase_challenge_doc(root, phase_report))})
        return 0
    if args.action == "review":
        print({"phase_manifest": phase_manifest(root), "phase_challenge_bundle": phase_challenge_bundle(root), "phase_review": phase_challenge_bundle(root)})
        return 0
    return 1
if __name__ == "__main__":
    raise SystemExit(main())
