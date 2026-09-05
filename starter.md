# Starter: using `continuity.db`

Read this first if you know nothing.

## Source of truth
- `continuity.db` is the main memory DB.
- `thinker/thinker.db` is auxiliary.
- `chat.db` is conversation-side data, not the main continuity store.

## Short summary surface
Use `v_core_model` for the compact four-layer model:
- state: observations, beliefs, convictions, open questions, decisions
- action: continuity requirements, work plans, steps, projects
- audit: receipts, reasoning episodes, version history, provenance
- policy: metacognitive state, influence modes, feature flags, epistemic tags, component influence

## Thinking engine / components
The thinking engine is mentioned via policy and component controls:
- `component_influence`
- `component_influence_modes`
- `component_influence_presets`
- `feature_flags`
- `epistemic_tags`

These are part of how the engine is tuned and steered, not core facts.

## Important entities
### State
- `beliefs` / `belief_versions`
- `convictions` / `conviction_versions` / `conviction_inputs`
- `open_questions`
- `observations`
- `decisions` / `v_decisions` for the current choice
- `decision_options` / `v_decision_options` for
  candidate options
- `decision_versions` / `v_decision_versions` for
  immutable history

### Action and planning
- `work_plans` / `work_plan_steps`
- `projects` (missions)
- `project-scoped goals` in `metacognitive_state` as `project_goal__<project_name>`
- `continuity_requirements` / `continuity_requirement_versions`

### Audit and structure
- `epistemic_receipts`
- `reasoning_episodes` / `reasoning_episode_inputs`
- `journal`
- `object_metadata` / `object_provenance`
- `concepts` / `concept_links` / `v_concept_search`

### Policy and posture
- `metacognitive_state` / `metacognitive_state_history`
- `ethical_principles` / `ethical_action_checks`
- `control_command_routes`

## Synthesis → policy promotion
When a synthesis is settled and should become an active rule, copy it into `metacognitive_state` instead of overwriting history.
- keep the original synthesis in `syntheses`
- write the active policy to `metacognitive_state`
- use the synthesis key as the policy key unless an explicit target key is needed
- do not replace an existing policy row unless asked to update it
- mark the synthesis `settled` so it stops disturbing default recall

## Current metacognitive state
Rows are keyed by `state_key`, with `category`, `value`, `confidence`, `provenance`, `version`, and `updated_at`.
Current key examples include `active_context_capsule`, `primary_goal`, `current_focus`, `active_project`, `current_project`, `current_aspect`, and persona/policy keys like `persona_system_analyst`.

Project goals are stored separately per mission, for example `project_goal__continuity_db`.

## Default retrieval order
1. `metacognitive_state` (`active_context_capsule`, `primary_goal`, `current_focus`, project goals)
2. `open_questions`
3. `beliefs` / `belief_versions`
4. `convictions` / `conviction_versions`
5. `syntheses`
6. `work_plans` / `work_plan_steps`
7. `projects` / `concepts` / `v_concept_search`
8. `journal`, `observations`, `decisions`, `v_decisions`, `decision_options`

## Current snapshot
- primary goal: maintain the durable continuity database, its policies, and auditable state
- current focus: coherent, auditable simulated mind
- active project: continuity_db
- continuity_db goal: `project_goal__continuity_db`
- default stance: use the DB as problem → goal → constraints → options → evidence → uncertainty → decision → next actions
  and keep the current choice, candidate options, and history in separate surfaces
- keep updates minimal, useful, and auditable
