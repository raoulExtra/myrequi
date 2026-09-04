from __future__ import annotations

from pathlib import Path


def write_phase_requirements_doc(root: Path, phase_report: list[dict[str, object]]) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    content = [
        "# Phase core requirements",
        "",
        "Each phase defines its own core requirements.",
        "AI should challenge them before the phase is treated as stable.",
        "",
        "## requirement types",
        "",
        "- `manual`: human checked, exception only.",
        "- `code`: code-first checked.",
        "- `auto_ai`: automation takes care of the AI-supported work.",
    ]
    for item in phase_report:
        content.extend([
            "",
            f"## {item['phase']}",
        ])
        if item['phase'] == 'phase_0.md':
            content.extend([f"- purpose: {item['purpose']}"])
        goals = item.get('goals') or ([] if not item.get('goal') else [item.get('goal')])
        if goals:
            content.append("- goals:")
            content.extend(f"  - {goal}" for goal in goals)
        content.extend([
            f"- outcome: {item['outcome']}",
            f"- status: {item['status']}",
        ])
        outcome_doc = item.get('outcome_doc')
        if outcome_doc:
            content.append(f"- outcome_doc: {outcome_doc}")
        content.extend([
            "",
            "### core requirements",
        ])
        requirements = item.get("core_requirements", [])
        if requirements:
            content.extend(f"- {req}" for req in requirements)
        else:
            content.append("- none")
    path = docs_dir / "phase-requirements.md"
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def write_phase_challenge_doc(root: Path, phase_report: list[dict[str, object]]) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    content = [
        "# Phase challenge prompts",
        "",
        "Ask AI to challenge every phase before it is treated as ready.",
        "",
        "## challenge rules",
        "",
        "1. Check that the phase has the right balance of purpose, goals, outcome, and status for its level.",
        "2. Check that core requirements are small, testable, non-overlapping, and typed.",
        "3. Ask whether the phase has too few or too many goals for the work it must carry.",
        "4. Capture fixes as doc changes, not hidden assumptions.",
    ]
    for item in phase_report:
        requirements = item.get("core_requirements", []) or ["none"]
        goals = item.get('goals') or ([] if not item.get('goal') else [item.get('goal')])
        content.extend([
            "",
            f"## {item['phase']}",
            "### AI challenge prompt",
            f"Challenge the requirements for {item['phase']}.",
        ])
        if item['phase'] == 'phase_0.md':
            content.append(f"Purpose: {item['purpose']}")
        else:
            content.append("Purpose: inherited from phase_0 and shaped by phase goals.")
            content.append("Goals:")
            content.extend(f"- {goal}" for goal in goals)
        content.extend([
            f"Outcome: {item['outcome']}",
            f"Status: {item['status']}",
            "Questions:",
            "- Are the core requirements specific enough to test?",
            "- Are any requirements duplicated, vague, missing, or the wrong type?",
            "- What future growth would break this phase definition?",
            "- Does the phase need more or fewer goals?",
            "- What should be added to make the phase future-proof?",
            "Current core requirements:",
        ])
        content.extend(f"- {req}" for req in requirements)
    path = docs_dir / "phase-challenge.md"
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def write_modularity_doc(root: Path, max_lines: int) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    content = [
        "# Modularity budget",
        "",
        f"The project keeps files at or below {max_lines} lines where practical.",
        "If a file grows beyond that budget, split it into smaller modules or docs.",
        "",
        "## check",
        "",
        "- `status` reports files over budget.",
        "- `budget` prints the same report on demand.",
        "- `checkpoint` and `advance` refuse to commit while over-budget files exist.",
        "",
        "## future-proofing",
        "",
        "- Use the budget as a warning before the file becomes hard to review.",
        "- Prefer smaller support files over one large growing file.",
        "- If a large generated file is necessary, document the exception explicitly.",
    ]
    path = docs_dir / "modularity.md"
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path
