# Phase challenge prompts

Ask AI to challenge every phase before it is treated as ready.

## challenge rules

1. Check that the phase has the right balance of purpose, goals, outcome, and status for its level.
2. Check that core requirements are small, testable, non-overlapping, and typed.
3. Ask whether the phase has too few or too many goals for the work it must carry.
4. Capture fixes as doc changes, not hidden assumptions.

## phase_0.md
### AI challenge prompt
Challenge the requirements for phase_0.md.
Purpose: self learning how to think sharp & structured
Outcome: a simple navigation page for the self_learn project.
Status: completed
Questions:
- Are the core requirements specific enough to test?
- Are any requirements duplicated, vague, missing, or the wrong type?
- What future growth would break this phase definition?
- Does the phase need more or fewer goals?
- What should be added to make the phase future-proof?
Current core requirements:
- [code] PH000-RC001: define the canonical project entry point.
- [code] PH000-RC002: keep the glossary and automation links visible.
- [code] PH000-RC003: preserve the phase boundary into phase 1.
- [code] PH000-RC004: describe the auto subproject and its versioned docs/implementation layout.
- [code] PH000-RC005: stay small enough to review quickly.

## phase_1.md
### AI challenge prompt
Challenge the requirements for phase_1.md.
Purpose: inherited from phase_0 and shaped by phase goals.
Goals:
- derive candidate self-learn paths from current files, glossary terms, and project state.
- rank candidate paths with explicit criteria, scores, and a short rationale.
- select one path and write the result into the phase outcome files.
Outcome: a ranked first-path brief with candidate comparison and selected next plan.
Status: active
Questions:
- Are the core requirements specific enough to test?
- Are any requirements duplicated, vague, missing, or the wrong type?
- What future growth would break this phase definition?
- Does the phase need more or fewer goals?
- What should be added to make the phase future-proof?
Current core requirements:
- [auto_ai] PH001-RC001: derive at least three candidate self-learn paths from the current project state and glossary.
- [auto_ai] PH001-RC002: score the candidates with explicit criteria, costs, and risks.
- [auto_ai] PH001-RC003: select one candidate and explain why it wins over the others.
- [auto_ai] PH001-RC004: write the selected path and review context into phase_1.md and docs/phase-1-outcome.md.

## phase_2.md
### AI challenge prompt
Challenge the requirements for phase_2.md.
Purpose: inherited from phase_0 and shaped by phase goals.
Goals:
- derive a phase 2 automation mission from phase 0 and phase 1 evidence.
- rank candidate missions with explicit criteria, cost, risk, and reuse.
- publish the selected mission as linked docs and durable metadata.
Outcome: derive the next automation mission from phase 0 and phase 1 evidence.
Status: active
Questions:
- Are the core requirements specific enough to test?
- Are any requirements duplicated, vague, missing, or the wrong type?
- What future growth would break this phase definition?
- Does the phase need more or fewer goals?
- What should be added to make the phase future-proof?
Current core requirements:
- [auto_ai] PH002-RC001: derive candidate mission paths from phase 0 and phase 1 evidence.
- [auto_ai] PH002-RC002: score and compare candidate paths with explicit criteria, costs, risks, and reuse.
- [auto_ai] PH002-RC003: write the selected mission into phase_2.md, docs/phase-2-mission.md, and docs/phase-2-outcome.md.
- [auto_ai] PH002-RC004: keep the mission reusable for later phases without rewriting historical record.
