# cognition.db

`continuity.db` is the SQLite-backed working memory
for this project: a structured store for beliefs,
convictions, decisions, questions, observations, plans,
syntheses, metacognitive state, requirements, and
policies.

`thinker/thinker.db` is a smaller companion database
for layered concept work.

## What it stores

- **Current state**: beliefs, convictions, concepts,
  decisions, open questions, observations, plans,
  personas, policies
- **History**: versioned belief and requirement tables
- **Audit**: immutable epistemic receipts and change
  logs
- **Interpretations**: convictions, syntheses,
  conflicts, evidence links, and reasoning episodes
- **Derived views**: recall, item links, explanation
  layers, provenance summary, and storage maps

## What changed recently

The DB now also models:

- **vision / mission / strategy / plan views**:
  `v_visions`, `v_missions`, `v_strategies`,
  `v_plans`
- **thinking patterns**:
  `constraint_first_thinking`,
  `battle_proven_thinking_way`,
  `reasoning_pattern_reuse_plan`,
  `core_thinking_patterns`
- **decision options**: `decision_options` and
  `v_decision_options` for side-by-side comparison
- **reasoning improvement tracking**:
  `CDB-13.8` and related patterns for before/after
  episode comparison
- **pattern reuse**: stored claim, concept,
  requirement, plan, episode, and arguments for
  reusable reasoning
- **thinking modes**: `persona_alien`,
  `persona_insect`, `persona_scholar`,
  `persona_skeptic`, `persona_builder`,
  `persona_moderator`, `persona_synthesizer`,
  `persona_super_ai`, `persona_system_analyst`
- **policy**: `thinking_policy` that rounds those
  modes into one operating view
- **quality**: first-class quality concept and linked
  quality-focused work plans
- **trust**: a first-class metacognitive stance that
  shapes evidence weighting and action
- **reasoning episodes**: auditable objects that keep
  claim, evidence, inference, uncertainty,
  reversibility, mode trail, and next action
- **tightened core model**: `v_core_model` as a
  compact four-layer summary of state, action, audit,
  and policy

These additions make the DB better at preserving not
just outputs, but also the path taken to reach them.

## Tightened core model

For day-to-day thinking, the DB works best when you
keep the core model small:

- **state**: observations, beliefs, convictions,
  open questions, decisions
- **action**: continuity requirements, work plans,
  steps, projects
- **audit**: receipts, reasoning episodes, version
  history, provenance
- **policy**: metacognitive state, influence modes,
  feature flags, epistemic tags

Everything else should usually be a view, alias, or
supporting metadata.

## Design goals

- Keep important state **auditable**
- Separate **current**, **history**, **evidence**, and
  **derived** data
- Preserve **continuity across turns**
- Make reasoning **inspectable** instead of hidden
- Support safe, incremental updates through scripts and
  validation
- Capture **how** a thought happened, not only what it
  concluded

## Main tables

- `beliefs` / `belief_versions`
- `convictions` / `conviction_versions` /
  `conviction_inputs`
- `continuity_requirements` /
  `continuity_requirement_versions`
- `metacognitive_state` /
  `metacognitive_state_history`
- `syntheses`, `synthesis_inputs`,
  `synthesis_conflicts`
- `decision_options`, `decisions`,
  `decision_versions`
- `object_metadata`, `object_provenance`,
  `epistemic_receipts`
- `work_plans`, `work_plan_steps`,
  `work_plan_links`
- `concepts`, `concept_links`
- `journal`, `observations`, `open_questions`,
  `reasoning_episodes`
- `projects` (missions)

## Derived views

- `v_visions` / `v_missions`
- `v_strategies` / `v_plans`
- `v_decision_options`
- `v_convictions`
- `v_items`
- `v_recall`
- `v_entry_points`
- `v_memory_index`
- `v_schema_catalog`
- `v_tag_search`
- `v_component_influence`
- `v_component_influence_presets`
- `v_component_influence_history`
- `v_component_influence_modes`
- `v_item_links`
- `error_recovery_influence_flow` work plan
- `evolved_baseline_demo` work plan
- `concept_links` for concept-to-plan relationships
- `v_explain`
- `v_interpreted_layer`
- `v_storage_map`
- `v_glossary_terms`
- `v_provenance_summary`

## Helper scripts

- `harden_continuity_db.py` — validates and maintains
  the main database contract
- `memory_command.py` — recall/search interface
- `plan_command.py` — lightweight goal, plan, and step
  tracking
- `scientist_command.py` — evidence-oriented analysis
  output
- `mode_command.py` — role/mode switching
- `code_tool.py` — trusted snippet execution backed by
  the DB

## What this DB might allow

If it works well, `continuity.db` could become more
than storage. It might support:

- **Long-horizon continuity**: remembering decisions,
  constraints, and unresolved questions across many
  turns
- **Auditable reasoning**: tracking what was observed,
  inferred, synthesized, or merely guessed
- **Better self-correction**: revising beliefs without
  losing the history of why they changed
- **Commitment discipline**: separating durable
  convictions from ordinary beliefs
- **Structured reflection**: separating facts,
  interpretations, uncertainties, and next actions
- **Plan continuity**: keeping work plans,
  dependencies, and follow-ups intact
- **Mission/strategy clarity**: exposing the path from
  vision to mission to strategy to plan
- **Concept growth**: building richer semantic
  structure around important ideas over time
- **Decision discipline**: comparing explicit options
  before choosing
- **Commitment discipline**: separating durable
  convictions from ordinary beliefs
- **Safer operation**: using explicit receipts,
  provenance, and review states instead of hidden
  state
- **Richer thinking**: using modes and personas to
  switch between exploration, skepticism,
  synthesis, execution, and discussion

In short, the database could let the system think in a
way that is:

- persistent
- inspectable
- versioned
- revisable
- more coherent over time
- easier to improve safely

## Thinker layer

`thinker/thinker.db` holds a smaller layered concept
model:

- `seeds`
- `jsons`
- `attribs`
- `concepts`
- `conc_sentence`

It supports a more abstract, layered view of concepts
and their descriptions.

## Notes

- This is a SQLite project; open the `.db` files with
  any SQLite client.
- For the canonical memory workspace, treat
  `continuity.db` as the source of truth.
- For thought-structure experiments, use
  `thinker/thinker.db`.
