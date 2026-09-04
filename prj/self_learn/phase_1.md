PROJECT PHASE 1
inherits_from: phase_0
goals:
- derive candidate self-learn paths from current files, glossary terms, and project state.
- rank candidate paths with explicit criteria, scores, and a short rationale.
- select one path and write the result into the phase outcome files.
outcome: a ranked first-path brief with candidate comparison and selected next plan.
outcome_doc: docs/phase-1-outcome.md

core_requirements:
- [auto_ai] PH001-RC001: derive at least three candidate self-learn paths from the current project state and glossary.
- [auto_ai] PH001-RC002: score the candidates with explicit criteria, costs, and risks.
- [auto_ai] PH001-RC003: select one candidate and explain why it wins over the others.
- [auto_ai] PH001-RC004: write the selected path and review context into phase_1.md and docs/phase-1-outcome.md.

output_contract:
- candidate_paths: derive at least three paths from current files and glossary terms.
- ranking: score every candidate with visible criteria and short rationale.
- selection: pick one winner and explain the tradeoffs against the others.
- output: write the result to phase_1.md and docs/phase-1-outcome.md.

## related plans
- [AI next-path phase plan](plans/4_plan.md)
- [Meta optimization plan](plans/7_plan.md)

navigation:
- [Project index](docs/index.md)
- [Glossary](docs/glossary.md)
- [Next path](docs/next-path.md)
- [Named phase 1 file](docs/phase-1-next-path.md)
- [Phase 1 core requi file](docs/phase-1-core-requi.md)
- [Phase 1 core review](docs/phase-1-core-review.md)
- [Phase 1 outcome](docs/phase-1-outcome.md)
- [Phase requirements](docs/phase-requirements.md)
- [Phase challenge](docs/phase-challenge.md)
- [Modularity budget](docs/modularity.md)
- [Phase 0](phase_0.md)
- [Phase 2](phase_2.md)
- [Automation notes](docs/automation.md)

status: active
