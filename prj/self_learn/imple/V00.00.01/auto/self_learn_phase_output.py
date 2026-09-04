from __future__ import annotations

from pathlib import Path

def phase_doc_path(root: Path, phase_number: int) -> Path:
    return root / f"phase_{phase_number}.md"


def phase_outcome_doc_path(root: Path, phase_number: int) -> Path:
    return root / "docs" / f"phase-{phase_number}-outcome.md"


def render_goals_section(goals: list[str]) -> str:
    return "\n".join(f"- {goal}" for goal in goals)


def phase_requirement_type(phase_number: int) -> str:
    return "code" if phase_number == 0 else "auto_ai"


def render_typed_core_requirements(phase_number: int, requirements: list[str]) -> list[str]:
    requirement_type = phase_requirement_type(phase_number)
    return [f"- [{requirement_type}] PH{phase_number:03d}-RC{index:03d}: {text}" for index, text in enumerate(requirements, start=1)]


def _phase_plan_links(phase_number: int) -> list[str]:
    if phase_number == 0:
        return [
            "- [Filesystem autonomy plan](plans/done/1_plan.md)",
            "- [Next-step automation plan](plans/done/2_plan.md)",
            "- [Glossary phase plan](plans/done/3_plan.md)",
            "- [AI next-path phase plan](plans/4_plan.md)",
            "- [Phase requirements plan](plans/done/5_plan.md)",
            "- [Phase review plan](plans/done/6_plan.md)",
            "- [Meta optimization plan](plans/7_plan.md)",
        ]
    if phase_number == 1:
        return [
            "- [AI next-path phase plan](plans/4_plan.md)",
            "- [Meta optimization plan](plans/7_plan.md)",
        ]
    return [
        "- [Meta optimization plan](plans/7_plan.md)",
    ]


def write_phase_outcome_doc(root: Path, phase_number: int, title: str, summary: str, details: list[str]) -> Path:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = phase_outcome_doc_path(root, phase_number)
    content = [
        f"# {title}",
        "",
        "## summary",
        summary,
        "",
        "## details",
    ]
    content.extend(details or ["- none recorded"])
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def _phase_0_body(root: Path, spec: dict[str, object], phase_report: list[dict[str, object]] | None, packet: dict[str, object] | None) -> list[str]:
    return [
        "",
        f"purpose: {spec['purpose']}",
        "",
        "## automation subproject",
        "- auto handles project automations.",
        "- it has docs/phase-0/auto/phase-0-core-requi-auto.md and docs/phase-0/auto/phase-0-core-review-auto.md as the canonical phase-0 auto companions.",
        "- the legacy flat aliases remain available during the transition.",
        "- it keeps the code in `imple/V00.00.01/auto/` and the companions in `docs/phase-0/auto/`.",
        "- phase 0 keeps this automation surface visible so the project can explain how it automates itself.",
        "",
        "tags:",
        "- thinking_workspace",
        "- self_learning",
        "",
        "## related plans",
        *_phase_plan_links(0),
        "",
        "navigation:",
        "- [Project index](docs/index.md)",
        "- [Glossary](docs/glossary.md)",
        "- [Next path](docs/next-path.md)",
        "- [Named phase 0 file](docs/phase-0-entry.md)",
        "- [Phase 0 core requi file](docs/phase-0-core-requi.md)",
        "- [Phase 0 core review](docs/phase-0-core-review.md)",
        "- [Phase 0 auto core requirements](docs/phase-0/auto/phase-0-core-requi-auto.md)",
        "- [Phase 0 auto core review](docs/phase-0/auto/phase-0-core-review-auto.md)",
        "- [Legacy auto core requirements](docs/phase-0-auto-core-requi.md)",
        "- [Legacy auto core review](docs/phase-0-auto-core-review.md)",
        "- [Phase 0 outcome](docs/phase-0-outcome.md)",
        "- [Phase requirements](docs/phase-requirements.md)",
        "- [Phase challenge](docs/phase-challenge.md)",
        "- [Modularity budget](docs/modularity.md)",
        "- [Working rules](docs/working-rules.md)",
        "- [Learning loop notes](docs/learning-loop.md)",
        "- [Filesystem autonomy notes](docs/filesystem-autonomy.md)",
        "- [Automation notes](docs/automation.md)",
        "- [Base project file organization standard](../base/002-requi-prj-file-organization-standard.md)",
        "- [Base phase 0](../base/phase_0.md)",
        "- [Phase 1](phase_1.md)",
        "",
        "glossary:",
        "- learning loop",
        "- self improvement",
        "- filespace",
        "- canonical",
        "- project",
        "- plan",
        "- path",
        "- suggestion",
        "- review",
        "- subproject",
        "- auto",
        "",
        f"status: {spec['status']}",
    ]


def _phase_1_body(root: Path, spec: dict[str, object], phase_report: list[dict[str, object]] | None, packet: dict[str, object] | None) -> list[str]:
    return [
        "",
        "output_contract:",
        "- candidate_paths: derive at least three paths from current files and glossary terms.",
        "- ranking: score every candidate with visible criteria and short rationale.",
        "- selection: pick one winner and explain the tradeoffs against the others.",
        "- output: write the result to phase_1.md and docs/phase-1-outcome.md.",
        "",
        "## related plans",
        *_phase_plan_links(1),
        "",
        "navigation:",
        "- [Project index](docs/index.md)",
        "- [Glossary](docs/glossary.md)",
        "- [Next path](docs/next-path.md)",
        "- [Named phase 1 file](docs/phase-1-next-path.md)",
        "- [Phase 1 core requi file](docs/phase-1-core-requi.md)",
        "- [Phase 1 core review](docs/phase-1-core-review.md)",
        "- [Phase 1 outcome](docs/phase-1-outcome.md)",
        "- [Phase requirements](docs/phase-requirements.md)",
        "- [Phase challenge](docs/phase-challenge.md)",
        "- [Modularity budget](docs/modularity.md)",
        "- [Phase 0](phase_0.md)",
        "- [Phase 2](phase_2.md)",
        "- [Automation notes](docs/automation.md)",
        "",
        f"status: {spec['status']}",
    ]


def _phase_history_lines(phase_report: list[dict[str, object]]) -> list[str]:
    lines = ["## phase history", ""]
    for item in phase_report:
        goals = item.get("goals") or ([] if not item.get("goal") else [item.get("goal")])
        lines.append(f"### {item['phase']}")
        if item['phase'] == 'phase_0.md':
            lines.append(f"- purpose: {item['purpose']}")
        else:
            previous_phase = f"phase_{int(item['phase'].split('_')[1].split('.')[0]) - 1}.md" if item['phase'].startswith('phase_') and item['phase'].split('_')[1].split('.')[0].isdigit() and int(item['phase'].split('_')[1].split('.')[0]) > 0 else 'phase_0.md'
            lines.append(f"- inherited from {previous_phase}")
        if goals:
            lines.append("- goals:")
            lines.extend(f"  - {goal}" for goal in goals)
        lines.extend([
            f"- outcome: {item['outcome']}",
            f"- status: {item['status']}",
            "",
        ])
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _phase_2_body(root: Path, spec: dict[str, object], phase_report: list[dict[str, object]] | None, packet: dict[str, object] | None) -> list[str]:
    packet = packet or {}
    ranked = packet.get("ranked_candidates", [])
    selected = packet.get("selected", {})
    lines = [
        "",
        "derived_learning_path:",
        f"- summary: {packet.get('summary', '')}",
        f"- selected: {selected.get('key', '')} ({selected.get('score', '')})" if selected else "- selected: ",
        f"- files: {', '.join(selected.get('files', []))}" if selected else "- files: ",
        f"- rationale: {packet.get('rationale', '')}",
        "",
        "## related plans",
        *_phase_plan_links(2),
        "",
        "ranking:",
    ]
    for index, candidate in enumerate(ranked, start=1):
        lines.append(f"- {index}. {candidate['key']} ({candidate['score']}): {candidate['path']}")
    lines.extend([
        "",
        "navigation:",
        "- [Project index](docs/index.md)",
        "- [Phase 0](phase_0.md)",
        "- [Phase 1](phase_1.md)",
        "- [Named phase 2 file](docs/phase-2-mission.md)",
        "- [Phase 2 outcome](docs/phase-2-outcome.md)",
        "- [Phase 2 core requi file](docs/phase-2-core-requi.md)",
        "- [Phase 2 core review](docs/phase-2-core-review.md)",
        "- [Phase requirements](docs/phase-requirements.md)",
        "- [Phase challenge](docs/phase-challenge.md)",
        "- [Modularity budget](docs/modularity.md)",
        "- [Working rules](docs/working-rules.md)",
        "- [Automation notes](docs/automation.md)",
        "",
        *_phase_history_lines(phase_report or []),
        "",
        f"status: {spec['status']}",
    ])
    return lines


PHASE_DOC_SPECS: dict[int, dict[str, object]] = {
    0: {
        "title": "PROJECT PHASE 0",
        "inherits_from": "base",
        "purpose": "self learning how to think sharp & structured",
        "goal": "use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path.",
        "goals": ["use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path."],
        "outcome": "a simple navigation page for the self_learn project.",
        "outcome_doc": "docs/phase-0-outcome.md",
        "status": "completed",
        "core_requirements": [
            "define the canonical project entry point.",
            "keep the glossary and automation links visible.",
            "preserve the phase boundary into phase 1.",
            "describe the auto subproject and its versioned docs/implementation layout.",
            "stay small enough to review quickly.",
        ],
        "body": _phase_0_body,
        "outcome_details": [
            "Purpose: self learning how to think sharp & structured.",
            "Goal: use the project to learn from interactions and keep the filespace coherent.",
            "Links: glossary, next path, phase 1, and supporting docs stay visible.",
            "Automation subproject: auto handles project automations through `imple/V00.00.01/auto/` with docs in `docs/phase-0/auto/`.",
        ],
    },
    1: {
        "title": "PROJECT PHASE 1",
        "inherits_from": "phase_0",
        "goals": [
            "derive candidate self-learn paths from current files, glossary terms, and project state.",
            "rank candidate paths with explicit criteria, scores, and a short rationale.",
            "select one path and write the result into the phase outcome files.",
        ],
        "outcome": "a ranked first-path brief with candidate comparison and selected next plan.",
        "outcome_doc": "docs/phase-1-outcome.md",
        "status": "active",
        "core_requirements": [
            "derive at least three candidate self-learn paths from the current project state and glossary.",
            "score the candidates with explicit criteria, costs, and risks.",
            "select one candidate and explain why it wins over the others.",
            "write the selected path and review context into phase_1.md and docs/phase-1-outcome.md.",
        ],
        "body": _phase_1_body,
        "outcome_details": [
            "Candidate set: at least three paths derived from current files, glossary terms, and project state.",
            "Ranking: every candidate must have visible criteria, scores, and a short reason.",
            "Selection: choose one path, explain why it wins, and name the rejected alternatives.",
            "Linked outputs: phase_1.md, docs/phase-1-next-path.md, and docs/phase-1-outcome.md must all tell the same story.",
        ],
    },
    2: {
        "title": "PROJECT PHASE 2",
        "inherits_from": "phase_1",
        "goals": [
            "derive a phase 2 automation mission from phase 0 and phase 1 evidence.",
            "rank candidate missions with explicit criteria, cost, risk, and reuse.",
            "publish the selected mission as linked docs and durable metadata.",
        ],
        "outcome": "derive the next automation mission from phase 0 and phase 1 evidence.",
        "outcome_doc": "docs/phase-2-outcome.md",
        "status": "active",
        "core_requirements": [
            "derive candidate mission paths from phase 0 and phase 1 evidence.",
            "score and compare candidate paths with explicit criteria, costs, risks, and reuse.",
            "write the selected mission into phase_2.md, docs/phase-2-mission.md, and docs/phase-2-outcome.md.",
            "keep the mission reusable for later phases without rewriting historical record.",
        ],
        "body": _phase_2_body,
        "outcome_details": [
            "Selected: P2-C1 (12)",
            "Rationale: phase 0 is use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path. and phase 1 is have AI suggest the first self-learn path with explicit criteria and a review loop., so the mission should join evidence into one automated choice.",
            "Files: docs/index.md, docs/glossary.md, docs/next-path.md, docs/automation.md, docs/phase-requirements.md, docs/phase-challenge.md, phase_0.md, phase_1.md, phase_2.md, docs/phase-0-outcome.md, docs/phase-1-outcome.md, docs/phase-2-outcome.md",
            "Ranking is preserved in phase_2.md and the linked mission doc.",
        ],
    },
}


def phase_doc_spec(phase_number: int) -> dict[str, object]:
    return PHASE_DOC_SPECS[phase_number]


def write_phase_doc(root: Path, phase_number: int, phase_report: list[dict[str, object]] | None = None, packet: dict[str, object] | None = None) -> Path:
    spec = phase_doc_spec(phase_number)
    path = phase_doc_path(root, phase_number)
    content = [
        spec["title"],
        f"inherits_from: {spec['inherits_from']}",
    ]
    purpose = spec.get("purpose")
    if purpose:
        content.append(f"purpose: {purpose}")
    goals = spec.get("goals") or []
    if goals:
        content.append("goals:")
        content.extend(render_goals_section(goals).splitlines())
    content.append(f"outcome: {spec['outcome']}")
    content.append(f"outcome_doc: {spec['outcome_doc']}")
    content.extend(["", "core_requirements:"])
    content.extend(render_typed_core_requirements(phase_number, list(spec.get("core_requirements", []))))
    body = spec["body"](root, spec, phase_report, packet)
    content.extend(body)
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    write_phase_outcome_doc(root, phase_number, f"Phase {phase_number} outcome", spec["outcome"], list(spec.get("outcome_details", [])))
    return path


def write_phase_0(root: Path) -> Path:
    return write_phase_doc(root, 0)


def write_phase_1(root: Path) -> Path:
    return write_phase_doc(root, 1)


def write_phase_2(root: Path, phase_report: list[dict[str, object]], packet: dict[str, object]) -> Path:
    return write_phase_doc(root, 2, phase_report=phase_report, packet=packet)
