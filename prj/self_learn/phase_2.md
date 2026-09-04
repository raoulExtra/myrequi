PROJECT PHASE 2
inherits_from: phase_1
goals:
- derive a phase 2 automation mission from phase 0 and phase 1 evidence.
- rank candidate missions with explicit criteria, cost, risk, and reuse.
- publish the selected mission as linked docs and durable metadata.
outcome: derive the next automation mission from phase 0 and phase 1 evidence.
outcome_doc: docs/phase-2-outcome.md

core_requirements:
- [auto_ai] PH002-RC001: derive candidate mission paths from phase 0 and phase 1 evidence.
- [auto_ai] PH002-RC002: score and compare candidate paths with explicit criteria, costs, risks, and reuse.
- [auto_ai] PH002-RC003: write the selected mission into phase_2.md, docs/phase-2-mission.md, and docs/phase-2-outcome.md.
- [auto_ai] PH002-RC004: keep the mission reusable for later phases without rewriting historical record.

derived_learning_path:
- summary: derive and rank the next automation mission from phase 0 and phase 1 evidence
- selected: P2-C1 (12)
- files: docs/index.md, docs/glossary.md, docs/next-path.md, docs/automation.md, docs/phase-requirements.md, docs/phase-challenge.md, phase_0.md, phase_1.md, phase_2.md, docs/phase-0-outcome.md, docs/phase-1-outcome.md, docs/phase-2-outcome.md
- rationale: phase 0 is use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path. and phase 1 is derive candidate self-learn paths from current files, glossary terms, and project state.; rank candidate paths with explicit criteria, scores, and a short rationale.; select one path and write the result into the phase outcome files., so the mission should join evidence into one automated choice.

## related plans
- [Meta optimization plan](plans/7_plan.md)

ranking:
- 1. P2-C1 (12): derive the next automation mission from phase 0 and phase 1 evidence
- 2. P2-C2 (10): verify requirement coverage and acceptance criteria for the phase docs
- 3. P2-C3 (6): stabilize refresh, checkpoint, and plan movement for future phases

navigation:
- [Project index](docs/index.md)
- [Phase 0](phase_0.md)
- [Phase 1](phase_1.md)
- [Named phase 2 file](docs/phase-2-mission.md)
- [Phase 2 outcome](docs/phase-2-outcome.md)
- [Phase 2 core requi file](docs/phase-2-core-requi.md)
- [Phase 2 core review](docs/phase-2-core-review.md)
- [Phase requirements](docs/phase-requirements.md)
- [Phase challenge](docs/phase-challenge.md)
- [Modularity budget](docs/modularity.md)
- [Working rules](docs/working-rules.md)
- [Automation notes](docs/automation.md)

## phase history

### phase_0.md
- purpose: self learning how to think sharp & structured
- goals:
  - use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path.
- outcome: a simple navigation page for the self_learn project.
- status: completed

### phase_1.md
- inherited from phase_0.md
- goals:
  - derive candidate self-learn paths from current files, glossary terms, and project state.
  - rank candidate paths with explicit criteria, scores, and a short rationale.
  - select one path and write the result into the phase outcome files.
- outcome: a ranked first-path brief with candidate comparison and selected next plan.
- status: active

### phase_2.md
- inherited from phase_1.md
- goals:
  - derive a phase 2 automation mission from phase 0 and phase 1 evidence.
  - rank candidate missions with explicit criteria, cost, risk, and reuse.
  - publish the selected mission as linked docs and durable metadata.
- outcome: derive the next automation mission from phase 0 and phase 1 evidence.
- status: active

status: active
