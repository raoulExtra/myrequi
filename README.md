# cognition.db

`cognition.db` is the SQLite-backed working memory for
this project: a structured store for beliefs,
decisions, questions, observations, plans, syntheses,
metacognitive state, and persona/mode policy.

In this repo, the main implementation lives in
`continuity.db`, with a smaller companion database in
`thinker/thinker.db` for layered concept work.

## What it stores

- **Current state**: beliefs, concepts, decisions,
  open questions, observations, plans, personas,
  policies
- **History**: versioned belief and requirement tables
- **Audit**: immutable epistemic receipts and change
  logs
- **Interpretations**: syntheses, conflicts, evidence
  links, and reasoning episodes
- **Derived views**: recall, item links, explanation
  layers, provenance summary, and storage maps

## What changed recently

The DB now also models:

- **thinking modes**: `persona_alien`,
  `persona_insect`, `persona_scholar`,
  `persona_skeptic`, `persona_builder`,
  `persona_moderator`, `persona_synthesizer`,
  `persona_super_ai`
- **policy**: `thinking_policy` that rounds those
  modes into one operating view
- **trust**: a first-class metacognitive stance that
  shapes evidence weighting and action
- **reasoning episodes**: auditable objects that keep
  claim, evidence, inference, uncertainty,
  reversibility, mode trail, and next action
- **moderator plans**: reusable discussion plans for
  thinking, democracy, and critical reasoning

These additions make the DB better at preserving not
just outputs, but also the path taken to reach them.

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
- `continuity_requirements` /
  `continuity_requirement_versions`
- `metacognitive_state` /
  `metacognitive_state_history`
- `syntheses`, `synthesis_inputs`,
  `synthesis_conflicts`
- `object_metadata`, `object_provenance`,
  `epistemic_receipts`
- `work_plans`, `work_plan_steps`,
  `work_plan_links`
- `concepts`, `concept_links`
- `journal`, `observations`, `decisions`,
  `open_questions`

## Derived views

- `v_items`
- `v_recall`
- `v_memory_index`
- `v_item_links`
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

If it works well, `cognition.db` could become more
than storage. It might support:

- **Long-horizon continuity**: remembering decisions,
  constraints, and unresolved questions across many
  turns
- **Auditable reasoning**: tracking what was observed,
  inferred, synthesized, or merely guessed
- **Better self-correction**: revising beliefs without
  losing the history of why they changed
- **Structured reflection**: separating facts,
  interpretations, uncertainties, and next actions
- **Plan continuity**: keeping work plans,
  dependencies, and follow-ups intact
- **Concept growth**: building richer semantic
  structure around important ideas over time
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
