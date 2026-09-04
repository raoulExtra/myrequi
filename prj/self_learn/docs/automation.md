# Automation

The self_learn project is meant to keep its own filesystem organized.

## current automation
- `imple/V00.00.01/self_learn_automation.py`
  - `sync`: create canonical dirs and move completed plans into `plans/done/`
  - `refresh`: sync and regenerate `docs/index.md`, `docs/glossary.md`, and `docs/next-path.md`
  - `advance`: refresh, write phase-1 docs, roll the project forward, and create a next-path plan
  - `checkpoint`: advance, stage `prj/self_learn` plus `continuity.db`, and commit
  - `status`: report the current filesystem shape

## future-proofing
- Keep the glossary small, canonical, and easy to extend.
- Add a new term before using it widely.
- Prefer updates that do not invalidate older docs.
- Keep phase 1 focused on AI choosing the first useful self-learn path.

## rule
When a plan becomes complete, move it into `plans/done/`.
