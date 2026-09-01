# Memory and filesystem guidance

## continuity.db
The demo project uses `continuity.db` for project-level memory and structure.
Typical data in the database includes:

- `projects`
- `project_activation_events`
- `project_objects`
- `project_requirements`

## filesystem
The demo project uses the filesystem for working project material and narrative guidance.
Typical filesystem-resident material includes:

- `phase_*.md` files for phase navigation
- `docs/` for guidance and explanations
- `examples/` for sample outputs or mock content
- `references/` for copied links to standards or specs
- `assets/` for images, diagrams, and screenshots
- `archive/` for old or superseded material
- `decisions/` for project-relevant decisions
- `plans/` for work plans and plan executions
- `imple/<version>/` for implementation snapshots
- `imple/<version>/test/` for implementation tests

## starter.md
Use `starter.md` as the short-form memory-db guide.
It says:

- `continuity.db` is the main memory DB
- keep state, plans, questions, and evidence auditable
- recall by relevance, confidence, and recency
- store durable strategy in the DB, not only in chat
