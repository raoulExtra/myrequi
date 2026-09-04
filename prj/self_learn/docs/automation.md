# Automation

The self_learn project is meant to keep its own filesystem organized.

## current automation
- `imple/V00.00.01/self_learn_automation.py`
  - wrapper entry point for the implementation split
- `imple/V00.00.01/self_learn_automation_core.py`
  - `sync`: create canonical dirs and move completed plans into `plans/done/`
  - `refresh`: sync, regenerate the docs, write `docs/meta-trace.json`, `docs/meta-optimization.md`, `docs/meta-actions.json`, `docs/meta-actions.md`, `docs/working-rules.md`, `docs/phase-0-entry.md`, `docs/phase-0-core-requi.md`, `docs/phase-0-core-review.md`, `docs/phase-1-next-path.md`, `docs/phase-1-core-requi.md`, `docs/phase-1-core-review.md`, and update `continuity.db`
  - `advance`: rewrite phase docs, roll the project forward, create the next automation plan, and refresh the docs
  - `checkpoint`: advance, then stage `prj/self_learn` plus `continuity.db`, and commit only when phase requirements and modularity budgets are clean
  - `status`: report the current filesystem shape, phase requirement coverage, meta trace, and any over-budget files
  - `budget`: print the modularity budget report on demand
  - `challenge`: regenerate the phase challenge prompt and print the manifest plus phase challenge bundle
  - `review`: print the manifest and review bundle for AI phase critique
  - `meta-trace.json`: machine-readable optimization trace for self-learning itself
  - `meta-optimization.md`: readable summary of the trace and recommendations
  - `meta-actions.json`: machine-readable self-correction actions
  - `meta-actions.md`: readable self-correction actions
  - `working-rules.md`: the current automation/testing rule of thumb
  - `phase-1-core-requi.md`: named phase 1 core requirements file
  - `phase-1-core-review.md`: named phase 1 review file

## future-proofing
- Keep the glossary small, canonical, and easy to extend.
- Add a new term before using it widely.
- Prefer updates that do not invalidate older docs.
- Keep phase definitions explicit and challenge them with AI.
- Split any file that grows beyond 700 lines into smaller modules or docs.

## rule
When a plan becomes complete, move it into `plans/done/`.
