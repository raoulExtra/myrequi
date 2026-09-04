from __future__ import annotations

from pathlib import Path

PHASE_1_CORE_REQUIREMENTS = [
    "derive at least one candidate self-learn path from the current project state.",
    "rank candidates with explicit criteria and a short rationale.",
    "review the selected path against the phase goal, outcome, and modularity budget.",
    "record feedback in docs and the meta trace so later phases can reuse it.",
]

PHASE_1_REVIEW_QUESTIONS = [
    "Does the phase produce candidate paths from current state, not from wishful thinking?",
    "Are the ranking criteria explicit, reviewable, and stable over time?",
    "Does the review record feedback and protect the modularity budget?",
    "Can the result be reused by the next plan without rewriting history?",
]


def write_named_phase_1_doc(root: Path) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "phase-1-next-path.md"
    content = """# Phase 1: next path

This is the named, human-friendly companion to `phase_1.md`.
It keeps the phase easy to browse like the named files in `prj/demo`.

## core requirements
- derive at least one candidate self-learn path from the current project state.
- rank candidates with explicit criteria and a short rationale.
- review the selected path against the phase goal, outcome, and modularity budget.
- record feedback in docs and the meta trace so later phases can reuse it.

## navigation
- [Phase 1](../phase_1.md)
- [Project index](./index.md)
- [Phase 1 core requirements](./phase-1-core-requi.md)
- [Phase 1 core review](./phase-1-core-review.md)
- [Phase requirements](./phase-requirements.md)
- [Phase challenge](./phase-challenge.md)
"""
    path.write_text(content, encoding="utf-8")
    return path


def write_phase_1_core_requi_doc(root: Path) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "phase-1-core-requi.md"
    content = [
        "# Phase 1 core requirements",
        "",
        "## core requirements",
    ]
    content.extend(f"- {req}" for req in PHASE_1_CORE_REQUIREMENTS)
    content.extend([
        "",
        "## use",
        "This file is the named, file-based summary of the phase 1 core requirements.",
        "It exists so the phase requirements have a stable companion file like `prj/demo`.",
    ])
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def write_phase_1_core_review_doc(root: Path) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "phase-1-core-review.md"
    content = [
        "# Phase 1 core review",
        "",
        "## review questions",
    ]
    content.extend(f"- {question}" for question in PHASE_1_REVIEW_QUESTIONS)
    content.extend([
        "",
        "## current view",
        "These core requirements are specific enough to test and future-proof because they produce paths, rank them, review them, and record feedback.",
        "",
        "## core requirements",
    ])
    content.extend(f"- {req}" for req in PHASE_1_CORE_REQUIREMENTS)
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path
