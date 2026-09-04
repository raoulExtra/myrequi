# Phase 2: mission

This is the named, human-friendly companion to `phase_2.md`.
It uses phase 0 and phase 1 history to define the current automation mission.

## core requirements
- PH002-RC001: derive the first concrete automation learning path from phase 0 and phase 1 evidence.
- PH002-RC002: rank the candidate paths with explicit criteria, costs, and risks.
- PH002-RC003: write the selected phase 2 mission into the filesystem and meta trace.
- PH002-RC004: keep the result reusable for later phases without rewriting history.

## acceptance criteria
### PH002-RC001
- PH002-RC001-AC001: the phase 0 and phase 1 history is summarized before choosing a path.
- PH002-RC001-AC002: the candidate paths come from current files and state, not from memory alone.

### PH002-RC002
- PH002-RC002-AC001: the ranking criteria are explicit, visible, and repeatable.
- PH002-RC002-AC002: the chosen path explains why it wins over the alternatives.

### PH002-RC003
- PH002-RC003-AC001: the selected mission is written into phase 2 docs and the meta trace.
- PH002-RC003-AC002: the mission can be revisited without changing the historical record.

### PH002-RC004
- PH002-RC004-AC001: the phase preserves a feedback loop for later learning phases.
- PH002-RC004-AC002: the docs remain small enough to review and regenerate quickly.

## mission summary
- summary: derive and rank the next automation mission from phase 0 and phase 1 evidence

## derived candidate paths

- P2-C1: derive the next automation mission from phase 0 and phase 1 evidence
  - evidence: phase 0 + phase 1 state
  - why: phase 0 is use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path. and phase 1 is have AI suggest the first self-learn path with explicit criteria and a review loop., so the mission should join evidence into one automated choice.
  - score: impact 5 + reuse 5 + testability 5 - cost 2 - risk 1 = 12
- P2-C2: verify requirement coverage and acceptance criteria for the phase docs
  - evidence: phase 0 + phase 1 state
  - why: phase 0 and phase 1 now use RC/AC codes, so the automation can prove coverage before selecting a deeper mission.
  - score: impact 4 + reuse 4 + testability 5 - cost 2 - risk 1 = 10
- P2-C3: stabilize refresh, checkpoint, and plan movement for future phases
  - evidence: phase 0 + phase 1 state
  - why: the project already regenerates many docs and commits phase state, so this path keeps the learning loop durable.
  - score: impact 3 + reuse 4 + testability 4 - cost 3 - risk 2 = 6

## ranking

1. P2-C1 (12) - derive the next automation mission from phase 0 and phase 1 evidence
   - why: phase 0 is use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path. and phase 1 is have AI suggest the first self-learn path with explicit criteria and a review loop., so the mission should join evidence into one automated choice.
2. P2-C2 (10) - verify requirement coverage and acceptance criteria for the phase docs
   - why: phase 0 and phase 1 now use RC/AC codes, so the automation can prove coverage before selecting a deeper mission.
3. P2-C3 (6) - stabilize refresh, checkpoint, and plan movement for future phases
   - why: the project already regenerates many docs and commits phase state, so this path keeps the learning loop durable.

## selected outcome
- P2-C1: derive the next automation mission from phase 0 and phase 1 evidence
- rationale: phase 0 is use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path. and phase 1 is have AI suggest the first self-learn path with explicit criteria and a review loop., so the mission should join evidence into one automated choice.

## navigation
- [Phase 2](../phase_2.md)
- [Project index](./index.md)
- [Phase 2 core requirements](./phase-2-core-requi.md)
- [Phase 2 core review](./phase-2-core-review.md)
- [Phase 1](../phase_1.md)
- [Phase requirements](./phase-requirements.md)
- [Phase challenge](./phase-challenge.md)

## phase history

### phase_0.md
- purpose: entry point for the self_learn project documentation.
- goal: use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path.
- outcome: a simple navigation page for the self_learn project.
- status: completed

### phase_1.md
- purpose: AI chooses the first useful self-learn path from the glossary and current project state.
- goal: have AI suggest the first self-learn path with explicit criteria and a review loop.
- outcome: a ranked first path that can be verified and turned into the next plan.
- status: active

### phase_2.md
- purpose: use phase 0 and phase 1 history to define the current automation mission.
- goal: have AI suggest the first concrete automation learning path from prior phase evidence.
- outcome: derive the next automation mission from phase 0 and phase 1 evidence.
- status: active
