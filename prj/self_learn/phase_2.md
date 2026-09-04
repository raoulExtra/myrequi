PROJECT PHASE 2
inherits_from: phase_1
purpose: use phase 0 and phase 1 history to define the current automation mission.
goal: have AI suggest the first concrete automation learning path from prior phase evidence.
outcome: derive the next automation mission from phase 0 and phase 1 evidence.

core_requirements:
- [auto_ai] PH002-RC001: derive the first concrete automation learning path from phase 0 and phase 1 evidence.
- [auto_ai] PH002-RC002: rank the candidate paths with explicit criteria, costs, and risks.
- [auto_ai] PH002-RC003: write the selected phase 2 mission into the filesystem and meta trace.
- [auto_ai] PH002-RC004: keep the result reusable for later phases without rewriting history.

derived_learning_path:
- summary: derive and rank the next automation mission from phase 0 and phase 1 evidence
- selected: P2-C1 (12)
- files: docs/index.md, docs/glossary.md, docs/next-path.md, docs/automation.md, docs/phase-requirements.md, docs/phase-challenge.md, phase_0.md, phase_1.md, phase_2.md
- rationale: phase 0 is use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path. and phase 1 is have AI suggest the first self-learn path with explicit criteria and a review loop., so the mission should join evidence into one automated choice.

ranking:
- 1. P2-C1 (12): derive the next automation mission from phase 0 and phase 1 evidence
- 2. P2-C2 (10): verify requirement coverage and acceptance criteria for the phase docs
- 3. P2-C3 (6): stabilize refresh, checkpoint, and plan movement for future phases

navigation:
- [Project index](docs/index.md)
- [Phase 0](phase_0.md)
- [Phase 1](phase_1.md)
- [Named phase 2 file](docs/phase-2-mission.md)
- [Phase 2 core requi file](docs/phase-2-core-requi.md)
- [Phase 2 core review](docs/phase-2-core-review.md)
- [Phase requirements](docs/phase-requirements.md)
- [Phase challenge](docs/phase-challenge.md)
- [Modularity budget](docs/modularity.md)
- [Working rules](docs/working-rules.md)
- [Automation notes](docs/automation.md)

phase_history:
- phase_0.md: entry point for the self_learn project documentation. | use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path. | a simple navigation page for the self_learn project.
- phase_1.md: AI chooses the first useful self-learn path from the glossary and current project state. | have AI suggest the first self-learn path with explicit criteria and a review loop. | a ranked first path that can be verified and turned into the next plan.
- phase_2.md: use phase 0 and phase 1 history to define the current automation mission. | have AI suggest the first concrete automation learning path from prior phase evidence. | derive the next automation mission from phase 0 and phase 1 evidence.

status: active
