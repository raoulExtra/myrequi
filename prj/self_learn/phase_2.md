PROJECT PHASE 2
inherits_from: phase_1
purpose: use phase 0 and phase 1 history to define the next AI mission for automation.
goal: have AI suggest a concrete automation learning path from prior phase evidence.
outcome: a ranked automation mission that can become the next durable plan.

core_requirements:
- PH002-RC001: derive candidate automation learning paths from phase 0 and phase 1 evidence.
- PH002-RC002: rank the candidate paths with explicit criteria, costs, and risks.
- PH002-RC003: write the selected phase 2 mission into the filesystem and meta trace.
- PH002-RC004: keep the result reusable for later phases without rewriting history.

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
- phase_2.md: use phase 0 and phase 1 history to define the next AI mission for automation. | have AI suggest a concrete automation learning path from prior phase evidence. | a ranked automation mission that can become the next durable plan.

status: planned
