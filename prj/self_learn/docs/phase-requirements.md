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
  - derive candidate self-learn paths from current files, glossary terms, and project state.
  - rank candidate paths with explicit criteria, scores, and a short rationale.
  - select one path and write the result into the phase outcome files.
- outcome: a ranked first-path brief with candidate comparison and selected next plan.
- status: active
- outcome_doc: docs/phase-1-outcome.md

### core requirements
- [auto_ai] PH001-RC001: derive at least three candidate self-learn paths from the current project state and glossary.
- [auto_ai] PH001-RC002: score the candidates with explicit criteria, costs, and risks.
- [auto_ai] PH001-RC003: select one candidate and explain why it wins over the others.
- [auto_ai] PH001-RC004: write the selected path and review context into phase_1.md and docs/phase-1-outcome.md.

## phase_2.md
- goals:
  - derive a phase 2 automation mission from phase 0 and phase 1 evidence.
  - rank candidate missions with explicit criteria, cost, risk, and reuse.
  - publish the selected mission as linked docs and durable metadata.
- outcome: derive the next automation mission from phase 0 and phase 1 evidence.
- status: active
- outcome_doc: docs/phase-2-outcome.md

### core requirements
- [auto_ai] PH002-RC001: derive candidate mission paths from phase 0 and phase 1 evidence.
- [auto_ai] PH002-RC002: score and compare candidate paths with explicit criteria, costs, risks, and reuse.
- [auto_ai] PH002-RC003: write the selected mission into phase_2.md, docs/phase-2-mission.md, and docs/phase-2-outcome.md.
- [auto_ai] PH002-RC004: keep the mission reusable for later phases without rewriting historical record.
