from __future__ import annotations

from pathlib import Path

PHASE_2_CORE_REQUIREMENTS = [
    "derive the first concrete automation learning path from phase 0 and phase 1 evidence.",
    "rank the candidate paths with explicit criteria, costs, and risks.",
    "write the selected phase 2 mission into the filesystem and meta trace.",
    "keep the result reusable for later phases without rewriting history.",
]

PHASE_2_ACCEPTANCE_CRITERIA = {
    1: [
        "the phase 0 and phase 1 history is summarized before choosing a path.",
        "the candidate paths come from current files and state, not from memory alone.",
    ],
    2: [
        "the ranking criteria are explicit, visible, and repeatable.",
        "the chosen path explains why it wins over the alternatives.",
    ],
    3: [
        "the selected mission is written into phase 2 docs and the meta trace.",
        "the mission can be revisited without changing the historical record.",
    ],
    4: [
        "the phase preserves a feedback loop for later learning phases.",
        "the docs remain small enough to review and regenerate quickly.",
    ],
}


def _phase_code(phase_number: int) -> str:
    return f"PH{phase_number:03d}"


def _requirement_code(phase_number: int, requirement_number: int) -> str:
    return f"{_phase_code(phase_number)}-RC{requirement_number:03d}"


def _acceptance_code(phase_number: int, requirement_number: int, criterion_number: int) -> str:
    return f"{_requirement_code(phase_number, requirement_number)}-AC{criterion_number:03d}"


def _render_core_requirements(phase_number: int, requirements: list[str]) -> list[str]:
    return [f"- {_requirement_code(phase_number, index)}: {text}" for index, text in enumerate(requirements, start=1)]


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


def derive_phase_2_candidates(phase_report: list[dict[str, object]]) -> list[dict[str, object]]:
    phase_0 = next((item for item in phase_report if item["phase"] == "phase_0.md"), None)
    phase_1 = next((item for item in phase_report if item["phase"] == "phase_1.md"), None)
    phase_0_goal = str(phase_0["goal"]) if phase_0 else ""
    phase_1_goal = str(phase_1["goal"]) if phase_1 else ""
    return [
        {
            "key": "P2-C1",
            "path": "derive the next automation mission from phase 0 and phase 1 evidence",
            "why": f"phase 0 is {phase_0_goal or 'the entry phase'} and phase 1 is {phase_1_goal or 'the path selection phase'}, so the mission should join evidence into one automated choice.",
            "impact": 5,
            "reuse": 5,
            "testability": 5,
            "cost": 2,
            "risk": 1,
        },
        {
            "key": "P2-C2",
            "path": "verify requirement coverage and acceptance criteria for the phase docs",
            "why": "phase 0 and phase 1 now use RC/AC codes, so the automation can prove coverage before selecting a deeper mission.",
            "impact": 4,
            "reuse": 4,
            "testability": 5,
            "cost": 2,
            "risk": 1,
        },
        {
            "key": "P2-C3",
            "path": "stabilize refresh, checkpoint, and plan movement for future phases",
            "why": "the project already regenerates many docs and commits phase state, so this path keeps the learning loop durable.",
            "impact": 3,
            "reuse": 4,
            "testability": 4,
            "cost": 3,
            "risk": 2,
        },
    ]


def rank_phase_2_candidates(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    ranked = []
    for candidate in candidates:
        score = int(candidate["impact"]) + int(candidate["reuse"]) + int(candidate["testability"]) - int(candidate["cost"]) - int(candidate["risk"])
        ranked.append({**candidate, "score": score})
    return sorted(ranked, key=lambda item: (-item["score"], -int(item["impact"]), -int(item["testability"]), item["key"]))


def select_phase_2_mission(phase_report: list[dict[str, object]]) -> dict[str, object]:
    candidates = derive_phase_2_candidates(phase_report)
    ranked = rank_phase_2_candidates(candidates)
    selected = ranked[0]
    return {
        "summary": "derive and rank the next automation mission from phase 0 and phase 1 evidence",
        "candidates": ranked,
        "ranked_candidates": ranked,
        "selected": selected,
        "outcome": selected["path"],
        "rationale": selected["why"],
    }


def _phase_history_lines(phase_report: list[dict[str, object]]) -> list[str]:
    lines = ["## phase history", ""]
    for item in phase_report:
        lines.extend([
            f"### {item['phase']}",
            f"- purpose: {item['purpose']}",
            f"- goal: {item['goal']}",
            f"- outcome: {item['outcome']}",
            f"- status: {item['status']}",
            "",
        ])
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _candidate_lines(packet: dict[str, object]) -> list[str]:
    lines = ["## derived candidate paths", ""]
    for candidate in packet["candidates"]:
        lines.extend([
            f"- {candidate['key']}: {candidate['path']}",
            f"  - evidence: phase 0 + phase 1 state",
            f"  - why: {candidate['why']}",
            f"  - score: impact {candidate['impact']} + reuse {candidate['reuse']} + testability {candidate['testability']} - cost {candidate['cost']} - risk {candidate['risk']} = {candidate['score']}",
        ])
    return lines


def _ranking_lines(packet: dict[str, object]) -> list[str]:
    lines = ["## ranking", ""]
    for index, candidate in enumerate(packet["ranked_candidates"], start=1):
        lines.extend([
            f"{index}. {candidate['key']} ({candidate['score']}) - {candidate['path']}",
            f"   - why: {candidate['why']}",
        ])
    lines.extend([
        "",
        "## selected outcome",
        f"- {packet['selected']['key']}: {packet['outcome']}",
        f"- rationale: {packet['rationale']}",
    ])
    return lines


def write_named_phase_2_doc(root: Path, phase_report: list[dict[str, object]]) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "phase-2-mission.md"
    packet = select_phase_2_mission(phase_report)
    content = [
        "# Phase 2: mission",
        "",
        "This is the named, human-friendly companion to `phase_2.md`.",
        "It uses phase 0 and phase 1 history to define the current automation mission.",
        "",
        "## core requirements",
    ]
    content.extend(_render_core_requirements(2, PHASE_2_CORE_REQUIREMENTS))
    content.extend([
        "",
        "## acceptance criteria",
    ])
    content.extend(_render_acceptance_criteria(2, PHASE_2_ACCEPTANCE_CRITERIA))
    content.extend(["", "## mission summary", f"- summary: {packet['summary']}"])
    content.extend(["", *_candidate_lines(packet), "", *_ranking_lines(packet)])
    content.extend([
        "",
        "## navigation",
        "- [Phase 2](../phase_2.md)",
        "- [Project index](./index.md)",
        "- [Phase 2 core requirements](./phase-2-core-requi.md)",
        "- [Phase 2 core review](./phase-2-core-review.md)",
        "- [Phase 1](../phase_1.md)",
        "- [Phase requirements](./phase-requirements.md)",
        "- [Phase challenge](./phase-challenge.md)",
    ])
    content.extend(["", *_phase_history_lines(phase_report)])
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def write_phase_2_core_requi_doc(root: Path, phase_report: list[dict[str, object]]) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "phase-2-core-requi.md"
    packet = select_phase_2_mission(phase_report)
    content = [
        "# Phase 2 core requirements",
        "",
        "## core requirements",
    ]
    content.extend(_render_core_requirements(2, PHASE_2_CORE_REQUIREMENTS))
    content.extend([
        "",
        "## acceptance criteria",
    ])
    content.extend(_render_acceptance_criteria(2, PHASE_2_ACCEPTANCE_CRITERIA))
    content.extend([
        "",
        "## use",
        "This file is the named, file-based summary of the phase 2 core requirements.",
        "It exists so the current automation mission can be carried forward from phase 0 and phase 1 evidence.",
        "",
        "## mission summary",
        f"- summary: {packet['summary']}",
        f"- outcome: {packet['outcome']}",
        "",
        "## phase history",
    ])
    for item in phase_report:
        content.extend([f"- {item['phase']}: {item['purpose']}"])
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def write_phase_2_core_review_doc(root: Path, phase_report: list[dict[str, object]]) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "phase-2-core-review.md"
    packet = select_phase_2_mission(phase_report)
    content = [
        "# Phase 2 core review",
        "",
        "## review questions",
        "- Does phase 2 use phase 0 and phase 1 evidence instead of inventing a new direction?",
        "- Are candidate missions ranked with explicit criteria and costs?",
        "- Does the result stay small, visible, and reusable?",
        "- Can the next phase build on this without losing history?",
        "",
        "## current view",
        f"Phase 2 should turn history into a ranked mission so the automation can learn from its own previous phases. The selected outcome is: {packet['outcome']}.",
        "",
        "## core requirements",
    ]
    content.extend(_render_core_requirements(2, PHASE_2_CORE_REQUIREMENTS))
    content.extend([
        "",
        "## ranking summary",
        f"- selected: {packet['selected']['key']}",
        f"- score: {packet['selected']['score']}",
        f"- rationale: {packet['rationale']}",
        "",
        "## phase history",
    ])
    for item in phase_report:
        content.extend([f"- {item['phase']}: {item['goal']}"])
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def write_phase_2(root: Path, phase_report: list[dict[str, object]]) -> Path:
    path = root / "phase_2.md"
    packet = select_phase_2_mission(phase_report)
    content = [
        "PROJECT PHASE 2",
        "inherits_from: phase_1",
        "purpose: use phase 0 and phase 1 history to define the current automation mission.",
        "goal: have AI suggest the first concrete automation learning path from prior phase evidence.",
        f"outcome: {packet['outcome']}.",
        "",
        "core_requirements:",
    ]
    content.extend(_render_core_requirements(2, PHASE_2_CORE_REQUIREMENTS))
    content.extend([
        "",
        "derived_learning_path:",
        f"- summary: {packet['summary']}",
        f"- selected: {packet['selected']['key']} ({packet['selected']['score']})",
        f"- rationale: {packet['rationale']}",
        "",
        "ranking:",
    ])
    for index, candidate in enumerate(packet["ranked_candidates"], start=1):
        content.extend([
            f"- {index}. {candidate['key']} ({candidate['score']}): {candidate['path']}",
        ])
    content.extend([
        "",
        "navigation:",
        "- [Project index](docs/index.md)",
        "- [Phase 0](phase_0.md)",
        "- [Phase 1](phase_1.md)",
        "- [Named phase 2 file](docs/phase-2-mission.md)",
        "- [Phase 2 core requi file](docs/phase-2-core-requi.md)",
        "- [Phase 2 core review](docs/phase-2-core-review.md)",
        "- [Phase requirements](docs/phase-requirements.md)",
        "- [Phase challenge](docs/phase-challenge.md)",
        "- [Modularity budget](docs/modularity.md)",
        "- [Working rules](docs/working-rules.md)",
        "- [Automation notes](docs/automation.md)",
        "",
        "phase_history:",
    ])
    for item in phase_report:
        content.extend([
            f"- {item['phase']}: {item['purpose']} | {item['goal']} | {item['outcome']}",
        ])
    content.extend([
        "",
        "status: active",
    ])
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path
