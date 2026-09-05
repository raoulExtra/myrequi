from __future__ import annotations

from pathlib import Path

PHASE_0_CORE_REQUIREMENTS = [
    "define the canonical project entry point.",
    "keep the glossary and automation links visible.",
    "preserve the phase boundary into phase 1.",
    "describe the auto subproject and its versioned docs/implementation layout.",
    "stay small enough to review quickly.",
]

PHASE_0_ACCEPTANCE_CRITERIA = {
    1: [
        "the entry point is obvious from the project root.",
        "the entry point stays named as the phase 0 home.",
    ],
    2: [
        "the glossary link is present in the visible navigation.",
        "the automation link is present in the visible navigation.",
    ],
    3: [
        "the phase 1 link remains visible and explicit.",
    ],
    4: [
        "the auto subproject is described as the place where project automations live.",
        "the versioned docs and implementation layout is mentioned explicitly.",
    ],
    5: [
        "the file stays short enough to scan quickly.",
    ],
}

PHASE_1_CORE_REQUIREMENTS = [
    "derive at least three candidate self-learn paths from the current project state and glossary.",
    "score the candidates with explicit criteria, costs, and risks.",
    "select one candidate and explain why it wins over the others.",
    "write the selected path and review context into phase_1.md and docs/phase-1-outcome.md.",
]

PHASE_1_ACCEPTANCE_CRITERIA = {
    1: [
        "a candidate path is written down from the current project state.",
        "the candidate path is derived from files, not from memory alone.",
    ],
    2: [
        "the ranking criteria are explicit and visible.",
        "the rationale explains why the chosen path wins.",
    ],
    3: [
        "the review checks the goal, outcome, and modularity budget.",
        "the review can say what should change if the path fails.",
    ],
    4: [
        "feedback is written back into docs or the meta trace.",
        "later phases can reuse the feedback without re-deriving it.",
    ],
}

PHASE_1_REVIEW_QUESTIONS = [
    "Does the phase produce at least three candidate paths from current state, not from wishful thinking?",
    "Are the ranking criteria explicit, reviewable, and stable over time?",
    "Does the review capture costs, risks, feedback, and the modularity budget?",
    "Can the selected path be reused by the next plan without rewriting history?",
]

ALLOWED_CORE_REQUIREMENT_TYPES = ("manual", "code", "auto_ai")


def _phase_code(phase_number: int) -> str:
    return f"PH{phase_number:03d}"


def _requirement_code(phase_number: int, requirement_number: int) -> str:
    return f"{_phase_code(phase_number)}-RC{requirement_number:03d}"


def _acceptance_code(phase_number: int, requirement_number: int, criterion_number: int) -> str:
    return f"{_requirement_code(phase_number, requirement_number)}-AC{criterion_number:03d}-AUTO"


def _core_requirement_type(phase_number: int) -> str:
    return "code" if phase_number == 0 else "auto_ai"


def _render_core_requirements(phase_number: int, requirements: list[str]) -> list[str]:
    requirement_type = _core_requirement_type(phase_number)
    return [f"- [{requirement_type}] {_requirement_code(phase_number, index)}: {text}" for index, text in enumerate(requirements, start=1)]


def _render_acceptance_criteria(phase_number: int, criteria_by_requirement: dict[int, list[str]]) -> list[str]:
    lines: list[str] = []
    for requirement_number in sorted(criteria_by_requirement):
        lines.append(f"### {_requirement_code(phase_number, requirement_number)}")
        for criterion_number, text in enumerate(criteria_by_requirement[requirement_number], start=1):
            lines.append(f"- {_acceptance_code(phase_number, requirement_number, criterion_number)}: {text}")
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _render_core_requirements_summary(phase_number: int, title: str, requirements: list[str]) -> list[str]:
    lines = [title, ""]
    lines.extend(_render_core_requirements(phase_number, requirements))
    return lines


def _type_legend() -> list[str]:
    return [
        "## type legend",
        "",
        "- `manual`: human checked, exception only.",
        "- `code`: mostly code checked.",
        "- `auto_ai`: automation drives the AI-supported work.",
    ]


def write_named_phase_0_doc(root: Path) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "phase-0-entry.md"
    content = [
        "# Phase 0: entry",
        "",
        "This is the named, human-friendly companion to `phase_0.md`.",
        "It keeps the entry phase easy to browse like the named files in `prj/demo`.",
        "",
        "## purpose",
        "- self learning how to think sharp & structured.",
        "",
        "## core requirements",
    ]
    content.extend(_render_core_requirements(0, PHASE_0_CORE_REQUIREMENTS))
    content.extend([
        "",
        "## acceptance criteria",
    ])
    content.extend(_render_acceptance_criteria(0, PHASE_0_ACCEPTANCE_CRITERIA))
    content.extend([
        "",
        "## related plans",
        "- [Filesystem autonomy plan](../plans/done/1_plan.md)",
        "- [Next-step automation plan](../plans/done/2_plan.md)",
        "- [Glossary phase plan](../plans/done/3_plan.md)",
        "- [AI next-path phase plan](../plans/4_plan.md)",
        "- [Phase requirements plan](../plans/done/5_plan.md)",
        "- [Phase review plan](../plans/done/6_plan.md)",
        "- [Meta optimization plan](../plans/7_plan.md)",
        "",
        "## navigation",
        "- [Phase 0](../phase_0.md)",
        "- [Phase 0 outcome](./phase-0-outcome.md)",
        "- [Project index](./index.md)",
        "- [Phase 0 core requirements](./phase-0-core-requi.md)",
        "- [Phase 0 core review](./phase-0-core-review.md)",
        "- [Phase 0 auto core requirements](./phase-0/auto/phase-0-core-requi-auto.md)",
        "- [Phase 0 auto core review](./phase-0/auto/phase-0-core-review-auto.md)",
        "- [Legacy auto core requirements](./phase-0-auto-core-requi.md)",
        "- [Legacy auto core review](./phase-0-auto-core-review.md)",
        "- [Phase 1](../phase_1.md)",
    ])
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def write_phase_0_core_requi_doc(root: Path) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "phase-0-core-requi.md"
    content = [
        "# Phase 0 core requirements",
        "",
        "## core requirements",
    ]
    content.extend(_render_core_requirements(0, PHASE_0_CORE_REQUIREMENTS))
    content.extend([
        "",
        "## acceptance criteria",
    ])
    content.extend(_render_acceptance_criteria(0, PHASE_0_ACCEPTANCE_CRITERIA))
    content.extend([
        "",
        "## use",
        "This file is the named, file-based summary of the phase 0 core requirements.",
        "It exists so the entry phase has a stable companion file like `prj/demo` and can point to `docs/phase-0/auto/phase-0-core-requi-auto.md`.",
    ])
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def write_phase_0_core_review_doc(root: Path) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "phase-0-core-review.md"
    content = [
        "# Phase 0 core review",
        "",
        "## review questions",
        "- Is the entry point canonical and obvious?",
        "- Are the glossary and automation links visible?",
        "- Is the auto subproject clearly identified as the home for project automations?",
        "- Does the versioned docs and implementation layout show up explicitly?",
        "- Does the file stay small and readable?",
        "- Does the phase boundary to phase 1 remain clear?",
        "",
        "## current view",
        "These core requirements are specific enough to test and future-proof because they keep the phase clean, visible, bounded, and linked to the automation subproject.",
        "",
        *_type_legend(),
        "",
        "## core requirements",
    ]
    content.extend(_render_core_requirements(0, PHASE_0_CORE_REQUIREMENTS))
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def write_phase_0_auto_core_requi_doc(root: Path) -> Path:
    docs_dir = root / "docs" / "phase-0" / "auto"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "phase-0-core-requi-auto.md"
    content = [
        "# Phase 0 auto core requirements",
        "",
        "## core requirements",
        "- [code] RC001-AUTO: define auto as the project automation subproject.",
        "- [code] RC002-AUTO: keep the versioned implementation layout under `imple/V00.00.01/auto/`.",
        "- [code] RC003-AUTO: keep a stable docs companion file for the auto subproject.",
        "- [code] RC004-AUTO: keep the auto documentation small and easy to review.",
        "- [code] RC005-AUTO: keep thin legacy wrappers at the old paths until migration is complete.",
        "- [code] RC006-AUTO: keep imports package-safe and self-contained inside `auto/`.",
        "- [code] RC007-AUTO: keep the CLI trigger surface stable for manual filesystem actions.",
        "- [code] RC008-AUTO: keep refresh and checkpoint able to regenerate and validate the auto docs.",
        "- [code] RC009-AUTO: keep tests covering both the canonical paths and the legacy aliases.",
        "- [code] RC010-AUTO: keep naming aligned across code, docs, and generated outputs.",
        "- [code] RC011-AUTO: keep auto as the canonical home for automation code and the related support files.",
        "",
        "## acceptance criteria",
        "### RC001-AUTO",
        "- RC001-AC001-AUTO: auto is described as the place where project automations live.",
        "- RC001-AC002-AUTO: the description stays visible in the phase 0 story.",
        "",
        "### RC002-AUTO",
        "- RC002-AC001-AUTO: the implementation path includes a versioned `auto/` directory.",
        "- RC002-AC002-AUTO: the versioned layout is explicit and reusable.",
        "",
        "### RC003-AUTO",
        "- RC003-AC001-AUTO: the docs companion file exists under `docs/phase-0/auto/`.",
        "- RC003-AC002-AUTO: the companion keeps the same close-to-phase naming pattern as the phase docs.",
        "",
        "### RC004-AUTO",
        "- RC004-AC001-AUTO: the file stays short enough to scan quickly.",
        "- RC004-AC002-AUTO: the file can be updated without breaking the older phase docs.",
        "",
        "### RC005-AUTO",
        "- RC005-AC001-AUTO: the old module paths still work during migration.",
        "- RC005-AC002-AUTO: the wrappers clearly point to the canonical `auto/` modules.",
        "",
        "### RC006-AUTO",
        "- RC006-AC001-AUTO: package-relative imports work inside the `auto/` folder.",
        "- RC006-AC002-AUTO: the modules do not depend on hidden path hacks.",
        "",
        "### RC007-AUTO",
        "- RC007-AC001-AUTO: the CLI keeps the known manual triggers available.",
        "- RC007-AC002-AUTO: filesystem management actions still work from the same command surface.",
        "",
        "### RC008-AUTO",
        "- RC008-AC001-AUTO: refresh regenerates the auto docs without manual fixes.",
        "- RC008-AC002-AUTO: checkpoint can validate the auto docs before committing.",
        "",
        "### RC009-AUTO",
        "- RC009-AC001-AUTO: tests cover the canonical auto paths.",
        "- RC009-AC002-AUTO: tests still cover the legacy aliases while they exist.",
        "",
        "### RC010-AUTO",
        "- RC010-AC001-AUTO: filenames, doc references, and generated outputs use the same naming scheme.",
        "- RC010-AC002-AUTO: the naming stays obvious enough for a future move or cleanup.",
        "",
        "### RC011-AUTO",
        "- RC011-AC001-AUTO: the canonical home stays under `imple/V00.00.01/auto/`.",
        "- RC011-AC002-AUTO: every canonical auto module lives in the `auto/` package.",
        "- RC011-AC003-AUTO: the legacy wrappers stay thin and temporary.",
        "- RC011-AC004-AUTO: package-relative imports work inside `auto/`.",
        "- RC011-AC005-AUTO: the CLI trigger surface stays stable for filesystem actions.",
        "- RC011-AC006-AUTO: refresh and checkpoint regenerate and validate the auto docs.",
        "- RC011-AC007-AUTO: tests cover canonical paths and legacy aliases.",
        "- RC011-AC008-AUTO: naming stays aligned across code, docs, and outputs.",
        "",
        "## use",
        "This is the canonical phase-0 auto requirements file.",
        "It mirrors the normal phase naming more closely as `docs/phase-0/auto/phase-0-core-requi-auto.md`.",
    ]
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    legacy = root / "docs" / "phase-0-auto-core-requi.md"
    legacy.write_text("\n".join([
        "# Legacy alias",
        "",
        "Canonical file: `docs/phase-0/auto/phase-0-core-requi-auto.md`.",
        "",
        "The new path keeps phase 0 and the auto subproject naming aligned.",
    ]) + "\n", encoding="utf-8")
    legacy2 = root / "docs" / "auto-core-requi.md"
    legacy2.write_text("\n".join([
        "# Legacy alias",
        "",
        "Canonical file: `docs/phase-0/auto/phase-0-core-requi-auto.md`.",
    ]) + "\n", encoding="utf-8")
    return path


def write_phase_0_auto_core_review_doc(root: Path) -> Path:
    docs_dir = root / "docs" / "phase-0" / "auto"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "phase-0-core-review-auto.md"
    content = [
        "# Phase 0 auto core review",
        "",
        "## review questions",
        "- Is auto clearly identified as the home for project automations?",
        "- Does the versioned docs and implementation layout show up explicitly?",
        "- Do the companion files use the phase-0/auto naming pattern?",
        "- Can the auto subproject grow without confusing the phase 0 story?",
        "- Is there a single canonical home for automation code and support files?",
        "- Do the old wrappers remain thin and temporary?",
        "- Are imports package-safe inside the `auto/` folder?",
        "- Does the CLI still expose the known filesystem management triggers?",
        "- Do refresh and checkpoint still regenerate and validate the auto docs?",
        "- Do the tests cover both canonical auto paths and legacy aliases?",
        "- Is the naming aligned across code, docs, and generated outputs?",
        "",
        "## current view",
        "These requirements keep the auto subproject visible, versioned, and easy to maintain alongside the phase 0 story.",
        "",
        *_type_legend(),
        "",
        "## core requirements",
        "- [code] RC001-AUTO: define auto as the project automation subproject.",
        "- [code] RC002-AUTO: keep the versioned implementation layout under `imple/V00.00.01/auto/`.",
        "- [code] RC003-AUTO: keep a stable docs companion file for the auto subproject.",
        "- [code] RC004-AUTO: keep the auto documentation small and easy to review.",
        "- [code] RC005-AUTO: keep thin legacy wrappers at the old paths until migration is complete.",
        "- [code] RC006-AUTO: keep imports package-safe and self-contained inside `auto/`.",
        "- [code] RC007-AUTO: keep the CLI trigger surface stable for manual filesystem actions.",
        "- [code] RC008-AUTO: keep refresh and checkpoint able to regenerate and validate the auto docs.",
        "- [code] RC009-AUTO: keep tests covering both the canonical paths and the legacy aliases.",
        "- [code] RC010-AUTO: keep naming aligned across code, docs, and generated outputs.",
        "- [code] RC011-AUTO: keep auto as the canonical home for automation code and the related support files.",
        "",
        "## acceptance criteria",
        "### RC001-AUTO",
        "- RC001-AC001-AUTO: auto is described as the place where project automations live.",
        "- RC001-AC002-AUTO: the description stays visible in the phase 0 story.",
        "",
        "### RC002-AUTO",
        "- RC002-AC001-AUTO: the implementation path includes a versioned `auto/` directory.",
        "- RC002-AC002-AUTO: the versioned layout is explicit and reusable.",
        "",
        "### RC003-AUTO",
        "- RC003-AC001-AUTO: the docs companion file exists under `docs/phase-0/auto/`.",
        "- RC003-AC002-AUTO: the companion keeps the same close-to-phase naming pattern as the phase docs.",
        "",
        "### RC004-AUTO",
        "- RC004-AC001-AUTO: the file stays short enough to scan quickly.",
        "- RC004-AC002-AUTO: the file can be updated without breaking the older phase docs.",
        "",
        "### RC005-AUTO",
        "- RC005-AC001-AUTO: the old module paths still work during migration.",
        "- RC005-AC002-AUTO: the wrappers clearly point to the canonical `auto/` modules.",
        "",
        "### RC006-AUTO",
        "- RC006-AC001-AUTO: package-relative imports work inside the `auto/` folder.",
        "- RC006-AC002-AUTO: the modules do not depend on hidden path hacks.",
        "",
        "### RC007-AUTO",
        "- RC007-AC001-AUTO: the CLI keeps the known manual triggers available.",
        "- RC007-AC002-AUTO: filesystem management actions still work from the same command surface.",
        "",
        "### RC008-AUTO",
        "- RC008-AC001-AUTO: refresh regenerates the auto docs without manual fixes.",
        "- RC008-AC002-AUTO: checkpoint can validate the auto docs before committing.",
        "",
        "### RC009-AUTO",
        "- RC009-AC001-AUTO: tests cover the canonical auto paths.",
        "- RC009-AC002-AUTO: tests still cover the legacy aliases while they exist.",
        "",
        "### RC010-AUTO",
        "- RC010-AC001-AUTO: filenames, doc references, and generated outputs use the same naming scheme.",
        "- RC010-AC002-AUTO: the naming stays obvious enough for a future move or cleanup.",
        "",
        "### RC011-AUTO",
        "- RC011-AC001-AUTO: the canonical home stays under `imple/V00.00.01/auto/`.",
        "- RC011-AC002-AUTO: every canonical auto module lives in the `auto/` package.",
        "- RC011-AC003-AUTO: the legacy wrappers stay thin and temporary.",
        "- RC011-AC004-AUTO: package-relative imports work inside `auto/`.",
        "- RC011-AC005-AUTO: the CLI trigger surface stays stable for filesystem actions.",
        "- RC011-AC006-AUTO: refresh and checkpoint regenerate and validate the auto docs.",
        "- RC011-AC007-AUTO: tests cover canonical paths and legacy aliases.",
        "- RC011-AC008-AUTO: naming stays aligned across code, docs, and outputs.",
        "",
        "## use",
        "This is the canonical phase-0 auto review file.",
        "It mirrors the normal phase naming more closely as `docs/phase-0/auto/phase-0-core-review-auto.md`.",
    ]
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    legacy = root / "docs" / "phase-0-auto-core-review.md"
    legacy.write_text("\n".join([
        "# Legacy alias",
        "",
        "Canonical file: `docs/phase-0/auto/phase-0-core-review-auto.md`.",
    ]) + "\n", encoding="utf-8")
    return path


def write_auto_prompt_core_requi_doc(root: Path) -> Path:
    docs_dir = root / "docs" / "phase-0" / "auto"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "auto-prompt-core-requi.md"
    content = [
        "# Auto prompt core requirements",
        "",
        "## core requirements",
        "- [code] RC012-AUTO: provide a lightweight prompt helper for automation questions.",
        "- [code] RC013-AUTO: support one-line questions without options.",
        "- [code] RC014-AUTO: support questions with numbered options.",
        "- [code] RC015-AUTO: support an optional note and default answer.",
        "- [code] RC016-AUTO: stay non-interactive-safe when stdin is not a TTY.",
        "- [code] RC017-AUTO: expose the prompt helper through the CLI trigger surface.",
        "",
        "## acceptance criteria",
        "### RC012-AUTO",
        "- RC012-AC001-AUTO: the helper lives under `auto/` and is importable as a package module.",
        "- RC012-AC002-AUTO: the helper does not depend on external libraries beyond the standard library.",
        "",
        "### RC013-AUTO",
        "- RC013-AC001-AUTO: a one-line question can be asked without options or defaults.",
        "- RC013-AC002-AUTO: the answer is returned as a plain string.",
        "",
        "### RC014-AUTO",
        "- RC014-AC001-AUTO: options are displayed as numbered choices.",
        "- RC014-AC002-AUTO: entering the option number returns the option text.",
        "",
        "### RC015-AUTO",
        "- RC015-AC001-AUTO: a note is printed before the prompt when provided.",
        "- RC015-AC002-AUTO: an empty input returns the default when one is set.",
        "",
        "### RC016-AUTO",
        "- RC016-AC001-AUTO: non-interactive mode reads `SELF_LEARN_ANSWER` from the environment.",
        "- RC016-AC002-AUTO: non-interactive mode falls back to the default when no env var is set.",
        "",
        "### RC017-AUTO",
        "- RC017-AC001-AUTO: the CLI exposes an `ask` subcommand with `--options`, `--note`, and `--default`.",
        "- RC017-AC002-AUTO: the CLI returns the answer as JSON.",
        "",
        "## use",
        "This file defines the requirements for the auto prompt helper.",
        "It keeps the interactive automation surface small and testable.",
    ]
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    legacy = root / "docs" / "auto-prompt-core-requi.md"
    legacy.write_text("\n".join([
        "# Legacy alias",
        "",
        "Canonical file: `docs/phase-0/auto/auto-prompt-core-requi.md`.",
    ]) + "\n", encoding="utf-8")
    return path


def write_auto_prompt_core_review_doc(root: Path) -> Path:
    docs_dir = root / "docs" / "phase-0" / "auto"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "auto-prompt-core-review.md"
    content = [
        "# Auto prompt core review",
        "",
        "## review questions",
        "- Is the prompt helper lightweight and stdlib-only?",
        "- Does it handle one-line questions, options, notes, and defaults?",
        "- Is non-interactive mode safe and predictable?",
        "- Is the CLI surface explicit and easy to script?",
        "- Can the helper be imported and reused inside other auto modules?",
        "",
        "## current view",
        "These requirements keep the interactive automation surface small, scriptable, and safe for both humans and non-interactive runs.",
        "",
        "## type legend",
        "",
        "- `manual`: human checked, exception only.",
        "- `code`: mostly code checked.",
        "- `auto_ai`: automation drives the AI-supported work.",
        "",
        "## core requirements",
        "- [code] RC012-AUTO: provide a lightweight prompt helper for automation questions.",
        "- [code] RC013-AUTO: support one-line questions without options.",
        "- [code] RC014-AUTO: support questions with numbered options.",
        "- [code] RC015-AUTO: support an optional note and default answer.",
        "- [code] RC016-AUTO: stay non-interactive-safe when stdin is not a TTY.",
        "- [code] RC017-AUTO: expose the prompt helper through the CLI trigger surface.",
        "",
        "## acceptance criteria",
        "### RC012-AUTO",
        "- RC012-AC001-AUTO: the helper lives under `auto/` and is importable as a package module.",
        "- RC012-AC002-AUTO: the helper does not depend on external libraries beyond the standard library.",
        "",
        "### RC013-AUTO",
        "- RC013-AC001-AUTO: a one-line question can be asked without options or defaults.",
        "- RC013-AC002-AUTO: the answer is returned as a plain string.",
        "",
        "### RC014-AUTO",
        "- RC014-AC001-AUTO: options are displayed as numbered choices.",
        "- RC014-AC002-AUTO: entering the option number returns the option text.",
        "",
        "### RC015-AUTO",
        "- RC015-AC001-AUTO: a note is printed before the prompt when provided.",
        "- RC015-AC002-AUTO: an empty input returns the default when one is set.",
        "",
        "### RC016-AUTO",
        "- RC016-AC001-AUTO: non-interactive mode reads `SELF_LEARN_ANSWER` from the environment.",
        "- RC016-AC002-AUTO: non-interactive mode falls back to the default when no env var is set.",
        "",
        "### RC017-AUTO",
        "- RC017-AC001-AUTO: the CLI exposes an `ask` subcommand with `--options`, `--note`, and `--default`.",
        "- RC017-AC002-AUTO: the CLI returns the answer as JSON.",
        "",
        "## use",
        "This is the canonical auto prompt review file.",
        "It keeps the prompt feature aligned with the auto subproject conventions.",
    ]
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    legacy = root / "docs" / "auto-prompt-core-review.md"
    legacy.write_text("\n".join([
        "# Legacy alias",
        "",
        "Canonical file: `docs/phase-0/auto/auto-prompt-core-review.md`.",
    ]) + "\n", encoding="utf-8")
    return path


def write_named_phase_1_doc(root: Path) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "phase-1-next-path.md"
    content = [
        "# Phase 1: next path",
        "",
        "This is the named, human-friendly companion to `phase_1.md`.",
        "It keeps the phase easy to browse like the named files in `prj/demo`.",
        "",
        "## core requirements",
    ]
    content.extend(_render_core_requirements(1, PHASE_1_CORE_REQUIREMENTS))
    content.extend([
        "",
        "## acceptance criteria",
    ])
    content.extend(_render_acceptance_criteria(1, PHASE_1_ACCEPTANCE_CRITERIA))
    content.extend([
        "",
        "## related plans",
        "- [AI next-path phase plan](../plans/4_plan.md)",
        "- [Meta optimization plan](../plans/7_plan.md)",
        "",
        "## navigation",
        "- [Phase 1](../phase_1.md)",
        "- [Phase 1 outcome](./phase-1-outcome.md)",
        "- [Project index](./index.md)",
        "- [Phase 1 core requirements](./phase-1-core-requi.md)",
        "- [Phase 1 core review](./phase-1-core-review.md)",
        "- [Phase requirements](./phase-requirements.md)",
        "- [Phase challenge](./phase-challenge.md)",
    ])
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
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
    content.extend(_render_core_requirements(1, PHASE_1_CORE_REQUIREMENTS))
    content.extend([
        "",
        "## acceptance criteria",
    ])
    content.extend(_render_acceptance_criteria(1, PHASE_1_ACCEPTANCE_CRITERIA))
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
        *_type_legend(),
        "",
        "## core requirements",
    ])
    content.extend(_render_core_requirements(1, PHASE_1_CORE_REQUIREMENTS))
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path
