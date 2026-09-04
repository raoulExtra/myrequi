# Active plan handoff
This file is generated when the project has an active plan.
It tells the next AI run what to do and where to store the result.
## active plans
### 4_plan.md
- title: Self-learn AI next-path phase plan
- source: plans/4_plan.md
- purpose: Have AI derive, score, and select self-learn paths from current project evidence, then write the chosen path into the phase 1 docs.
- steps:
  - 1. Derive at least three candidate paths from the current project state and glossary.
  - 2. Score each candidate with explicit criteria, costs, and risks.
  - 3. Select one winner and explain why it beats the others.
  - 4. Write the selected path and review context into `phase_1.md` and `docs/phase-1-outcome.md`.
- outcome store: plans/done/4_plan_exec_<timestamp>.md
- completion rule: update the source plan to status: completed, then let sync move it into plans/done/.

### 7_plan.md
- title: Self-learn meta optimization plan
- source: plans/7_plan.md
- purpose: Automate the trace of self-learning optimization so the project can see its own improvement signals.
- when to run:
  - run when a new active plan appears or an active plan changes.
  - run after refresh, checkpoint, or phase updates that change plan/state visibility.
  - run before using the meta trace to decide the next automation move.
- steps:
  - 1. Generate a meta optimization trace from phase state and modularity signals.
  - 2. Persist the trace in docs and continuity.db.
  - 3. Use the trace to guide the next self-learning review.
  - 4. Keep the trace format small and durable.
- outcome store: plans/done/7_plan_exec_<timestamp>.md
- completion rule: update the source plan to status: completed, then let sync move it into plans/done/.

## rule
- Run the active plan before creating the next checkpoint.
- Store the outcome in a dedicated execution record under `plans/done/`.
- Keep the execution record readable and small.
