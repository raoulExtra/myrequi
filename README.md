# cognition.db

`cognition.db` is the SQLite-backed working memory for
this project: a structured store for beliefs,
decisions, questions, observations, plans, syntheses,
and metacognitive state.

In this repo, the main implementation lives in
`continuity.db`, with a smaller companion database in
`thinker/thinker.db` for layered concept work.

## What it stores

- **Current state**: beliefs, concepts, decisions,
  open questions, observations, plans
- **History**: versioned belief and requirement tables
- **Audit**: immutable epistemic receipts and change
  logs
- **Interpretations**: syntheses, conflicts, and
  evidence links
- **Derived views**: recall, item links, explanation
  layers, and storage maps

## Design goals

- Keep important state **auditable**
- Separate **current**, **history**, **evidence**, and
  **derived** data
- Preserve **continuity across turns**
- Make reasoning **inspectable** instead of hidden
- Support safe, incremental updates through scripts and
  validation

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

## Helper scripts

- `harden_continuity_db.py` — validates and maintains
  the main database contract
- `memory_command.py` — recall/search interface
- `scientist_command.py` — evidence-oriented analysis
  output
- `mode_command.py` — role/mode switching
- `code_tool.py` — trusted snippet execution backed by
  the DB

## What this DB might allow

If it works well, `cognition.db` could become more than
storage. It might support:

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

In short, the database could let the system think in a
way that is:

- persistent
- inspectable
- versioned
- revisable
- more coherent over time

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
