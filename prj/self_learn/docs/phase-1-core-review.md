# Phase 1 core review

## review questions
- Does the phase produce at least three candidate paths from current state, not from wishful thinking?
- Are the ranking criteria explicit, reviewable, and stable over time?
- Does the review capture costs, risks, feedback, and the modularity budget?
- Can the selected path be reused by the next plan without rewriting history?

## current view
These core requirements are specific enough to test and future-proof because they produce paths, rank them, review them, and record feedback.

## type legend

- `manual`: human checked, exception only.
- `code`: mostly code checked.
- `auto_ai`: automation drives the AI-supported work.

## core requirements
- [auto_ai] PH001-RC001: derive at least three candidate self-learn paths from the current project state and glossary.
- [auto_ai] PH001-RC002: score the candidates with explicit criteria, costs, and risks.
- [auto_ai] PH001-RC003: select one candidate and explain why it wins over the others.
- [auto_ai] PH001-RC004: write the selected path and review context into phase_1.md and docs/phase-1-outcome.md.
