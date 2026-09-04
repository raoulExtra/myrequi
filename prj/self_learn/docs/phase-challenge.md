# Phase challenge prompts

Ask AI to challenge every phase before it is treated as ready.

## challenge rules

1. Check that purpose, goal, outcome, and status are all explicit.
2. Check that core requirements are small, testable, non-overlapping, and typed.
3. Ask what would break the phase definition as the project grows.
4. Capture fixes as doc changes, not hidden assumptions.

## phase_0.md
### AI challenge prompt
Challenge the requirements for phase_0.md.
Purpose: entry point for the self_learn project documentation.
Goal: use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path.
Outcome: a simple navigation page for the self_learn project.
Status: completed
Questions:
- Are the core requirements specific enough to test?
- Are any requirements duplicated, vague, missing, or the wrong type?
- What future growth would break this phase definition?
- What should be added to make the phase future-proof?
Current core requirements:
- [code] PH000-RC001: define the canonical project entry point.
- [code] PH000-RC002: keep the glossary and automation links visible.
- [code] PH000-RC003: preserve the phase boundary into phase 1.
- [code] PH000-RC004: stay small enough to review quickly.

## phase_1.md
### AI challenge prompt
Challenge the requirements for phase_1.md.
Purpose: AI chooses the first useful self-learn path from the glossary and current project state.
Goal: have AI suggest the first self-learn path with explicit criteria and a review loop.
Outcome: a ranked first path that can be verified and turned into the next plan.
Status: active
Questions:
- Are the core requirements specific enough to test?
- Are any requirements duplicated, vague, missing, or the wrong type?
- What future growth would break this phase definition?
- What should be added to make the phase future-proof?
Current core requirements:
- [auto_ai] PH001-RC001: derive at least one candidate self-learn path from the current project state.
- [auto_ai] PH001-RC002: rank candidates with explicit criteria and a short rationale.
- [auto_ai] PH001-RC003: review the selected path against the phase goal, outcome, and modularity budget.
- [auto_ai] PH001-RC004: record feedback in docs and the meta trace so later phases can reuse it.

## phase_2.md
### AI challenge prompt
Challenge the requirements for phase_2.md.
Purpose: use phase 0 and phase 1 history to define the current automation mission.
Goal: have AI suggest the first concrete automation learning path from prior phase evidence.
Outcome: derive the next automation mission from phase 0 and phase 1 evidence.
Status: active
Questions:
- Are the core requirements specific enough to test?
- Are any requirements duplicated, vague, missing, or the wrong type?
- What future growth would break this phase definition?
- What should be added to make the phase future-proof?
Current core requirements:
- [auto_ai] PH002-RC001: derive the first concrete automation learning path from phase 0 and phase 1 evidence.
- [auto_ai] PH002-RC002: rank the candidate paths with explicit criteria, costs, and risks.
- [auto_ai] PH002-RC003: write the selected phase 2 mission into the filesystem and meta trace.
- [auto_ai] PH002-RC004: keep the result reusable for later phases without rewriting history.
