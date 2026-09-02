# Starter: using `continuity.db`

Read this first if you know nothing.

## Source of truth
- Use `continuity.db` as the main memory DB.
- Treat `thinker/thinker.db` as auxiliary.

## Important entities

### Core state
- `metacognitive_state` / `metacognitive_state_history`
- `open_questions`
- `work_plans` / `work_plan_steps`
- `journal`
- `projects` (missions)

### Claims and commitments
- `beliefs` / `belief_versions`
- `convictions` / `conviction_versions` / `conviction_inputs`
- `syntheses` / `synthesis_inputs` / `synthesis_conflicts`
- `reasoning_episodes` / `reasoning_episode_inputs`
- `arguments` / `argument_claim_links`

### Evidence and audit
- `observations`
- `decisions` / `decision_versions`
- `decision_options`
- `epistemic_receipts`
- `object_metadata` / `object_provenance`

### Structure and policy
- `concepts` / `concept_links`
- `continuity_requirements`
- `ethical_principles` / `ethical_action_checks`
- `control_command_routes`

## Default retrieval order
1. `metacognitive_state` (`primary_goal`, `current_focus`)
2. `open_questions`
3. `beliefs` / `belief_versions`
4. `convictions` / `conviction_versions`
5. `syntheses` / `synthesis_conflicts`
6. `work_plans` / `work_plan_steps`
7. `projects` / `concepts`
8. `journal`, `observations`, `decisions`, `decision_options`

## Recall rules
- Recall by **relevance + confidence + recency**.
- Use `condition` when something should surface only in a matching context.
- Use `scope` for where it is valid.
- Prefer concise, explicit summaries over raw internal reasoning.

## What to store where
- **beliefs**: stable claims
- **convictions**: durable commitments and working judgments
- **arguments**: support and opposition for beliefs
- **syntheses**: merged conclusions
- **open_questions**: unresolved prompts/blockers
- **work_plans**: active plans and thinking prompts
- **projects**: missions / long-running objectives
- **concepts**: reusable patterns and ideas
- **decision_options**: candidate choices for a decision
- **metacognitive_state**: current goal, focus, posture
- **journal**: short progress notes

## Thinking prompt pattern
- Put the prompt text in `work_plans.prompt`.
- Give it a clear `title` and `objective`.
- Add `condition` if it should only surface sometimes.
- Use `convictions` for durable commitments.
- Use `projects` for missions and `metacognitive_state` for vision.
- Use `concepts` for reusable strategies and patterns.
- Recall it with `memory_command.py recall <query>`.

## Clear role mapping
- vision -> `metacognitive_state`
- mission -> `projects`
- conviction -> `convictions`
- strategy -> `concepts`
- plan -> `work_plans`

## Useful commands
```bash
python3 memory_command.py recall "<query>" --db continuity.db
python3 plan_command.py status --db continuity.db
python3 plan_command.py goal set "<goal>" --db continuity.db
```

## Rule of thumb
- If it should last: store it.
- If it is uncertain: mark confidence low.
- If it is conditional: add `condition`.
- If it is actionable: make it a plan or open question.
