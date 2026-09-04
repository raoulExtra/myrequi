# Phase challenge prompts

Ask AI to challenge every phase before it is treated as ready.

## challenge rules

1. Check that purpose, goal, outcome, and status are all explicit.
2. Check that core requirements are small, testable, and non-overlapping.
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
- Are any requirements duplicated, vague, or missing?
- What future growth would break this phase definition?
- What should be added to make the phase future-proof?
Current core requirements:
- define the canonical project entry point.
- keep the glossary and automation links visible.
- preserve the phase boundary into phase 1.
- stay small enough to review quickly.

## phase_1.md
### AI challenge prompt
Challenge the requirements for phase_1.md.
Purpose: AI chooses the first useful self-learn path from the glossary and current project state.
Goal: have AI suggest the first self-learn path with explicit criteria and a review loop.
Outcome: a ranked first path that can be verified and turned into the next plan.
Status: active
Questions:
- Are the core requirements specific enough to test?
- Are any requirements duplicated, vague, or missing?
- What future growth would break this phase definition?
- What should be added to make the phase future-proof?
Current core requirements:
- derive at least one candidate self-learn path from the current project state.
- rank candidates with explicit criteria and a short rationale.
- review the selected path against the phase goal, outcome, and modularity budget.
- record feedback in docs and the meta trace so later phases can reuse it.

## phase_2.md
### AI challenge prompt
Challenge the requirements for phase_2.md.
Purpose: use phase 0 and phase 1 history to define the next AI mission for automation.
Goal: have AI suggest a concrete automation learning path from prior phase evidence.
Outcome: a ranked automation mission that can become the next durable plan.
Status: planned
Questions:
- Are the core requirements specific enough to test?
- Are any requirements duplicated, vague, or missing?
- What future growth would break this phase definition?
- What should be added to make the phase future-proof?
Current core requirements:
- PH002-RC001: derive candidate automation learning paths from phase 0 and phase 1 evidence.
- PH002-RC002: rank the candidate paths with explicit criteria, costs, and risks.
- PH002-RC003: write the selected phase 2 mission into the filesystem and meta trace.
- PH002-RC004: keep the result reusable for later phases without rewriting history.
