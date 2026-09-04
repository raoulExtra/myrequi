# Phase core requirements

Each phase defines its own core requirements.
AI should challenge them before the phase is treated as stable.

## requirement types

- `manual`: human checked, exception only.
- `code`: code-first checked.
- `auto_ai`: automation takes care of the AI-supported work.

## phase_0.md
- purpose: self learning how to think sharp & structured
- goals:
  - use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path.
- goal: use the project to learn from interactions, improve tools, keep the filespace coherent, learn how to think sharp, collect a future-proof glossary, and suggest the first self-learn path.
- outcome: a simple navigation page for the self_learn project.
- status: completed
- outcome_doc: docs/phase-0-outcome.md

### core requirements
- [code] PH000-RC001: define the canonical project entry point.
- [code] PH000-RC002: keep the glossary and automation links visible.
- [code] PH000-RC003: preserve the phase boundary into phase 1.
- [code] PH000-RC004: stay small enough to review quickly.

## phase_1.md
- goals:
  - have AI suggest the first self-learn path with explicit criteria and a review loop.
- goal: have AI suggest the first self-learn path with explicit criteria and a review loop.
- outcome: a ranked first path that can be verified and turned into the next plan.
- status: active
- outcome_doc: docs/phase-1-outcome.md

### core requirements
- [auto_ai] PH001-RC001: derive at least one candidate self-learn path from the current project state.
- [auto_ai] PH001-RC002: rank candidates with explicit criteria and a short rationale.
- [auto_ai] PH001-RC003: review the selected path against the phase goals, outcome, and modularity budget.
- [auto_ai] PH001-RC004: record feedback in docs and the meta trace so later phases can reuse it.

## phase_2.md
- goals:
  - have AI suggest the first concrete automation learning path from prior phase evidence.
- goal: have AI suggest the first concrete automation learning path from prior phase evidence.
- outcome: derive the next automation mission from phase 0 and phase 1 evidence.
- status: active
- outcome_doc: docs/phase-2-outcome.md

### core requirements
- [auto_ai] PH002-RC001: derive the first concrete automation learning path from phase 0 and phase 1 evidence.
- [auto_ai] PH002-RC002: rank the candidate paths with explicit criteria, costs, and risks.
- [auto_ai] PH002-RC003: write the selected phase 2 mission into the filesystem and meta trace.
- [auto_ai] PH002-RC004: keep the result reusable for later phases without rewriting history.
