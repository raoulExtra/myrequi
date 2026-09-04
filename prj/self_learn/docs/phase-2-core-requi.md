# Phase 2 core requirements

## core requirements
- [auto_ai] PH002-RC001: derive the first concrete automation learning path from phase 0 and phase 1 evidence.
- [auto_ai] PH002-RC002: rank the candidate paths with explicit criteria, costs, and risks.
- [auto_ai] PH002-RC003: write the selected phase 2 mission into the filesystem and meta trace.
- [auto_ai] PH002-RC004: keep the result reusable for later phases without rewriting history.

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

## use
This file is the named, file-based summary of the phase 2 core requirements.
It exists so the current automation mission can be carried forward from phase 0 and phase 1 evidence.

## mission summary
- summary: derive and rank the next automation mission from phase 0 and phase 1 evidence
- outcome: derive the next automation mission from phase 0 and phase 1 evidence

## phase history
- phase_0.md: entry point for the self_learn project documentation.
- phase_1.md: AI chooses the first useful self-learn path from the glossary and current project state.
- phase_2.md: use phase 0 and phase 1 history to define the current automation mission.
