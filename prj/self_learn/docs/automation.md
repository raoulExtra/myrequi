# Automation

The self_learn project is meant to keep its own filesystem organized.

## current automation
- `imple/V00.00.01/self_learn_automation.py`
  - `sync`: create canonical dirs and move completed plans into `plans/done/`
  - `refresh`: sync and regenerate `docs/index.md`, `docs/glossary.md`, `docs/next-path.md`, `docs/phase-requirements.md`, `docs/phase-challenge.md`, and `docs/modularity.md`
  - `advance`: rewrite phase docs, roll the project forward, create the next automation plan, and refresh the docs
  - `checkpoint`: advance, then stage `prj/self_learn` plus `continuity.db`, and commit only when phase requirements and modularity budgets are clean
  - `status`: report the current filesystem shape, phase requirement coverage, and any over-budget files
  - `budget`: print the modularity budget report on demand
  - `challenge`: regenerate the phase challenge prompt and print the current phase requirement report

## future-proofing
- Keep the glossary small, canonical, and easy to extend.
- Add a new term before using it widely.
- Prefer updates that do not invalidate older docs.
- Keep phase definitions explicit and challenge them with AI.
- Split any file that grows beyond 700 lines into smaller modules or docs.

## rule
When a plan becomes complete, move it into `plans/done/`.
