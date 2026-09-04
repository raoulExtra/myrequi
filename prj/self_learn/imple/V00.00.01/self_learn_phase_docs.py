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
    ]
    for item in phase_report:
        content.extend([
            "",
            f"## {item['phase']}",
            f"- purpose: {item['purpose']}",
            f"- goal: {item['goal']}",
            f"- outcome: {item['outcome']}",
            f"- status: {item['status']}",
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
        "1. Check that purpose, goal, outcome, and status are all explicit.",
        "2. Check that core requirements are small, testable, and non-overlapping.",
        "3. Ask what would break the phase definition as the project grows.",
        "4. Capture fixes as doc changes, not hidden assumptions.",
    ]
    for item in phase_report:
        requirements = item.get("core_requirements", []) or ["none"]
        content.extend([
            "",
            f"## {item['phase']}",
            "### AI challenge prompt",
            f"Challenge the requirements for {item['phase']}.",
            f"Purpose: {item['purpose']}",
            f"Goal: {item['goal']}",
            f"Outcome: {item['outcome']}",
            f"Status: {item['status']}",
            "Questions:",
            "- Are the core requirements specific enough to test?",
            "- Are any requirements duplicated, vague, or missing?",
            "- What future growth would break this phase definition?",
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
