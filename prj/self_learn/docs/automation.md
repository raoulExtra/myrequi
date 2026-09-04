# Automation

The self_learn project is meant to keep its own filesystem organized.

## current automation
- `imple/V00.00.01/self_learn_automation.py`
  - wrapper entry point for the implementation split
- `imple/V00.00.01/self_learn_automation_core.py`
  - `sync`: create canonical dirs, promote ready plans from `plans/prep/` into `plans/`, and move completed plans into `plans/done/`
  - `refresh`: sync, regenerate the docs, write `docs/meta-trace.json`, `docs/meta-optimization.md`, `docs/meta-actions.json`, `docs/meta-actions.md`, `docs/active-plan.md`, `docs/working-rules.md`, `docs/phase-0-entry.md`, `docs/phase-0-core-requi.md`, `docs/phase-0-core-review.md`, `docs/phase-1-next-path.md`, `docs/phase-1-core-requi.md`, `docs/phase-1-core-review.md`, `docs/phase-2-mission.md`, `docs/phase-2-core-requi.md`, `docs/phase-2-core-review.md`, and update `continuity.db`
  - `write_active_plan_handoff`: describe the current active plan, when to run it, and the exact storage path for its result
  - `write_plan_execution_record`: store the completed AI run in `plans/done/` with a timestamped execution file
  - `advance`: rewrite phase docs, roll the project forward, create the next automation plan, and refresh the docs
  - `checkpoint`: advance, then stage `prj/self_learn` plus `continuity.db`, and commit only when phase requirements and modularity budgets are clean
  - `status`: report the current filesystem shape, phase requirement coverage, meta trace, and any over-budget files
  - `budget`: print the modularity budget report on demand
  - `challenge`: regenerate the phase challenge prompt and print the manifest plus phase challenge bundle
  - `review`: print the manifest and review bundle for AI phase critique
  - file info for AI: when no concrete file list is available, use the smallest useful fileset related to the phase
  - `meta-trace.json`: machine-readable optimization trace for self-learning itself
  - `meta-optimization.md`: readable summary of the trace and recommendations
  - `meta-actions.json`: machine-readable self-correction actions
  - `meta-actions.md`: readable self-correction actions
  - `working-rules.md`: the current automation/testing rule of thumb
  - `phase-1-core-requi.md`: named phase 1 core requirements file
  - `phase-1-core-review.md`: named phase 1 review file
  - `phase-2-mission.md`: named phase 2 mission file (current automation mission)
  - `phase-2-core-requi.md`: named phase 2 core requirements file
  - `phase-2-core-review.md`: named phase 2 review file

## future-proofing
- Keep the glossary small, canonical, and easy to extend.
- Add a new term before using it widely.
- Prefer updates that do not invalidate older docs.
- Keep phase definitions explicit and challenge them with AI.
- Make phase 0 purpose prominent and link phase-related plans from the phase docs.
- Split any file that grows beyond 700 lines into smaller modules or docs.

## rule
When a plan is active, generate a handoff doc and run it before the next checkpoint.
When a plan is in `plans/prep/` and its run trigger is ready, promote it into `plans/` so it can run.
When a plan becomes complete, store a dedicated execution record in `plans/done/` and move the source plan into `plans/done/`.
