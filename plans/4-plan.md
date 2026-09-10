# Read Helpful Things from the DB

- file: 4-plan.md
- kind: human_generated

## Name
Read Helpful Things from the DB

## Source
- continuity.db usage
- user collaborative loop

## Objective
Use continuity.db as a source of helpful knowledge: retrieve relevant beliefs, decisions, concepts, plans, and reasoning episodes to inform current work, avoid repeating mistakes, and reuse proven patterns.

## DB Query Results (from Step x)

> Full content lives in [db_support.md](plans/prep/001-plan-base-db-support.md). 

## Steps

### 1. Initialize Work Plan (One‑time)
- [x] Create a work plan entry in `continuity.db` (table `work_plans`) for the base project, including:
  - `plan_key`: "base_project_consolidation"
  - `topic`: "Base Project Consolidation"
  - `goal`: "Consolidate base project together with the user in a loop"
  - `status`: "active"
  - `created_at`: current timestamp
  - `updated_at`: current timestamp
- [x] Add an initial `open_questions` entry to capture any early ambiguities.

### 2. Retrieve Current Project State
- [x] Query `beliefs`, `decisions`, `work_plans`, and `open_questions` tables for the base project's existing context.
- [x] Summarize key items in a short markdown snippet (see DB Query Results above).

### 3. Present Summary to User
- [ ] Display the summary to the user and ask for:
  - Priorities for consolidation (e.g., which modules, files, or concepts to focus on).
  - Any new requirements or constraints.
  - Desired level of granularity (high‑level vs. detailed).

### 4. Refine Plan & Record Decisions
- [ ] Based on user input, create or update:
  - `decisions` entries (table `decisions`) describing the agreed consolidation actions.
  - `work_plan_steps` (within the `work_plans` entry) listing concrete next steps.
  - `beliefs` or `convictions` if new foundational assumptions are made.
- [ ] Attach relevant evidence (e.g., file references, code snippets) to the decision record.

### 5. Save and Record Reasoning Episode
- [ ] Write a `reasoning_episode` entry (table `reasoning_episodes`) describing:
  - The loop iteration's purpose.
  - User's input and your interpretation.
  - The decisions made and the updated plan.
  - Timestamp and any confidence rating.
- [ ] Mark the work plan status as `active` if further iterations are needed, or `completed` when consolidation criteria are met.

### 6. Loop Until Consolidation Criteria Are Met
- [ ] After each iteration, ask the user if the current plan satisfies the consolidation goal or if another round is needed.
- [ ] If more work is required, return to step 2 to re‑fetch the updated state, otherwise finalize.

## Notes
- All state changes must be recorded in `continuity.db`; this ensures traceability and enables auditability.
- Use the `open_questions` table to capture any unresolved items after each loop.
- Keep `work_plan_steps` short (3‑7 actionable items) to maintain focus.
- The loop should be explicit: each cycle is a "consolidation round" with a clear start and end.
- The `user_interaction` concept (`concept: user_interaction`) is now the canonical first-contact entry point for understanding how this agent interacts with users.

## Priority Order
1. Initialize work plan entry in `continuity.db`.
2. Retrieve and summarize current project state from DB (beliefs, decisions, concepts).
3. Present summary and gather user input.
4. Refine plan, record decisions, and update work steps.
5. Save reasoning episode and obtain user confirmation.
6. Iterate until consolidation criteria are satisfied.

## Status
planned