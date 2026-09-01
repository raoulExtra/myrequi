# Memory and filesystem guidance

## continuity.db: project information

The database stores project-level structure and relationships in these tables:

- `projects` — project identity, display name, hierarchy, active flag, and description
- `project_activation_events` — history of project activation changes
- `project_objects` — project links to objects it owns, contains, tracks, or supports
- `project_requirements` — requirements linked to a project if 
those are connected to the db

For example, the `demo` project is stored in `projects` with its parent project, description, and active status. It also has a `project_objects` link to `thinking_project`.

## Filesystem: project information

The filesystem stores the working documentation and implementation layout for each project:

- `phase_*.md` files at the project root for phase navigation and inheritance
- `docs/` for narrative guidance and explanations
- `examples/` for sample outputs or mock content
- `references/` for copied links to standards or specs
- `assets/` for images, diagrams, and screenshots
- `archive/` for old or superseded material
- `decisions/` for project-relevant decisions
- `plans/` for work_plan templates and executions
- `imple/<version>/` for implementation snapshots
- `imple/<version>/test/` for tests of that implementation version

## Starter guidance

Use `starter.md` as the short-form memory guide:

- `continuity.db` is the main memory DB
- keep state, plans, questions, and evidence auditable
- recall by relevance, confidence, and recency
- store durable strategy in the DB, not only in chat

## Practical rule

The filesystem should have all info about the project.

Examples for filesystem infos: 
phase docs, examples, implementation snapshots,
 tests, or narrative guidance.

If it is project identity, hierarchy, ownership
or activation history, it also can be found in `continuity.db`.
