# Phase 1 core review

## review questions
- Does the phase produce candidate paths from current state, not from wishful thinking?
- Are the ranking criteria explicit, reviewable, and stable over time?
- Does the review record feedback and protect the modularity budget?
- Can the result be reused by the next plan without rewriting history?

## current view
These core requirements are specific enough to test and future-proof because they produce paths, rank them, review them, and record feedback.

## type legend

- `manual`: human checked, exception only.
- `code`: mostly code checked.
- `auto_ai`: automation drives the AI-supported work.

## core requirements
- [auto_ai] PH001-RC001: derive at least one candidate self-learn path from the current project state.
- [auto_ai] PH001-RC002: rank candidates with explicit criteria and a short rationale.
- [auto_ai] PH001-RC003: review the selected path against the phase goal, outcome, and modularity budget.
- [auto_ai] PH001-RC004: record feedback in docs and the meta trace so later phases can reuse it.
