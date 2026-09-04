from __future__ import annotations

import argparse
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

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
    ("objective", "The reason a plan or project exists.", "Usually broader than a step and narrower than a mission."),
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

PHASE1_PLAN_KEY = "4_plan.md"
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
    return moved


def sync(root: Path = PROJECT_ROOT) -> SyncReport:
    created_dirs = ensure_canonical_dirs(root)
    moved_plans = move_completed_plans(root)
    return SyncReport(created_dirs=created_dirs, moved_plans=moved_plans)


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


def write_phase_0(root: Path = PROJECT_ROOT) -> Path:
    path = root / "phase_0.md"
    content = """PROJECT PHASE 0
inherits_from: base
purpose: entry point for the self_learn project documentation.
goal: use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path.
outcome: a simple navigation page for the self_learn project.

tags:
- thinking_workspace
- self_learning

navigation:
- [Project index](docs/index.md)
- [Glossary](docs/glossary.md)
- [Next path](docs/next-path.md)
- [Learning loop notes](docs/learning-loop.md)
- [Filesystem autonomy notes](docs/filesystem-autonomy.md)
- [Automation notes](docs/automation.md)
- [Glossary phase plan](plans/done/3_plan.md)
- [Base project file organization standard](../base/002-requi-prj-file-organization-standard.md)
- [Base phase 0](../base/phase_0.md)
- [Phase 1](phase_1.md)

glossary:
- learning loop
- self improvement
- filespace
- canonical
- project
- plan
- path
- suggestion
- review

status: completed
"""
    path.write_text(content, encoding="utf-8")
    return path


def write_phase_1(root: Path = PROJECT_ROOT) -> Path:
    path = root / "phase_1.md"
    content = """PROJECT PHASE 1
inherits_from: phase_0
purpose: AI chooses the first useful self-learn path from the glossary and current project state.
goal: have AI suggest the first self-learn path with explicit criteria and a review loop.
outcome: a ranked first path that can be verified and turned into the next plan.

navigation:
- [Project index](docs/index.md)
- [Glossary](docs/glossary.md)
- [Next path](docs/next-path.md)
- [Phase 0](phase_0.md)
- [Automation notes](docs/automation.md)
- [Next path plan](plans/4_plan.md)

status: active
"""
    path.write_text(content, encoding="utf-8")
    return path


def write_readme(root: Path = PROJECT_ROOT) -> Path:
    path = root / "README.md"
    content = """# self_learn

Project entry point.

- [Project index](docs/index.md)
- [Glossary](docs/glossary.md)
- [Next path](docs/next-path.md)
- [Phase 0](phase_0.md)
- [Phase 1](phase_1.md)
- [Filesystem autonomy](docs/filesystem-autonomy.md)
- [Automation](docs/automation.md)
"""
    path.write_text(content, encoding="utf-8")
    return path


def write_next_phase_plan(root: Path = PROJECT_ROOT) -> Path:
    plans_dir = root / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    path = plans_dir / PHASE1_PLAN_KEY
    content = f"""# Self-learn AI next-path phase plan

status: active

## objective
Have AI suggest the first self-learn path using the future-proof glossary and current project state.

## steps
1. Compare candidate paths against explicit criteria.
2. Rank suggestions by priority and reviewability.
3. Capture feedback from the chosen path.
4. Turn the best path into the next concrete plan.
"""
    path.write_text(content, encoding="utf-8")
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
    return {
        "root": str(root),
        "dirs": [str((root / rel).relative_to(root)) + "/" for rel in CANONICAL_DIRS if (root / rel).exists()],
        "phases": sorted(p.name for p in root.glob("phase_*.md")),
        "active_plans": active_plans,
        "done_plans": done_plans,
        "docs": sorted(p.name for p in (root / "docs").glob("*.md")) if (root / "docs").exists() else [],
        "docs_index": str(root / "docs" / "index.md") if (root / "docs" / "index.md").exists() else None,
    }


def refresh(root: Path = PROJECT_ROOT) -> dict[str, object]:
    report = sync(root)
    glossary_path = write_glossary(root)
    next_path_doc = write_next_path_doc(root)
    index_path = docs_index(root)
    return {**report.as_dict(), "glossary": str(glossary_path), "next_path": str(next_path_doc), "docs_index": str(index_path)}


def advance(root: Path = PROJECT_ROOT) -> dict[str, object]:
    report = refresh(root)
    phase_0 = write_phase_0(root)
    phase_1 = write_phase_1(root)
    readme = write_readme(root)
    next_plan = write_next_phase_plan(root)
    phase3 = root / "plans" / "3_plan.md"
    if phase3.exists():
        target = root / "plans" / "done" / phase3.name
        target.parent.mkdir(parents=True, exist_ok=True)
        text = _read_text(phase3)
        if "status: completed" not in text.lower():
            if "status: active" in text:
                text = text.replace("status: active", "status: completed", 1)
            else:
                text = text.replace("## objective", "status: completed\n\n## objective", 1)
            phase3.write_text(text, encoding="utf-8")
        shutil.move(str(phase3), str(target))
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
    goal = "Use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path."
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "update metacognitive_state set value=?, version=?, updated_at=CURRENT_TIMESTAMP where state_key='project_goal__self_learn'",
            (goal, 4),
        )
        conn.commit()
    finally:
        conn.close()


def git_checkpoint(root: Path = PROJECT_ROOT, message: str = "self_learn: filesystem checkpoint") -> dict[str, object]:
    repo_root = _repo_root(root)
    rel_root = str(root.resolve().relative_to(repo_root))
    subprocess.run(["git", "-C", str(repo_root), "add", rel_root, "continuity.db"], check=True)
    diff = subprocess.run(["git", "-C", str(repo_root), "diff", "--cached", "--quiet"])
    if diff.returncode == 0:
        return {"repo_root": str(repo_root), "staged": [], "committed": False, "message": message}
    subprocess.run(["git", "-C", str(repo_root), "commit", "-m", message], check=True)
    rev = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"], check=True, capture_output=True, text=True)
    return {"repo_root": str(repo_root), "staged": [rel_root, "continuity.db"], "committed": True, "message": message, "commit": rev.stdout.strip()}


def checkpoint(root: Path = PROJECT_ROOT, message: str = "self_learn: filesystem checkpoint") -> dict[str, object]:
    report = advance(root)
    return {**report, "git": report["git"], "checkpoint": message}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Self-learn filesystem automation helper")
    parser.add_argument("action", choices=["sync", "refresh", "advance", "checkpoint", "status"])
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
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
