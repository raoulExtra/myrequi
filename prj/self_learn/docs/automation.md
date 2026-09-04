# Automation

The self_learn project is meant to keep its own filesystem organized.

## current automation
- `imple/V00.00.01/self_learn_automation.py`
  - `sync`: create canonical dirs and move completed plans into `plans/done/`
  - `refresh`: sync and regenerate `docs/index.md`
  - `checkpoint`: refresh, stage `prj/self_learn` plus `continuity.db`, and commit
  - `status`: report the current filesystem shape

## future-proofing
- Keep the glossary small, canonical, and easy to extend.
- Add a new term before using it widely.
- Prefer updates that do not invalidate older docs.

## rule
When a plan becomes complete, move it into `plans/done/`.
