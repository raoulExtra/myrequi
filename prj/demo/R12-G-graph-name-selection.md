'''yaml
title: R12-G-graph-name-selection
requirement_id: R12-G
phase: phase_1_1
for_version: default_version
'''

# R12-G: Graph tool can select a graph by name

The demo project SHALL allow graph names to be provided in the graph JSON under `name`. The loader SHALL store that name with the graph when present. The demo project SHALL also provide a `--name` argument that resolves a graph by its stored JSON name, source-file name, or filename stem and uses that graph wherever graph selection is needed. The `--name` selection SHALL work for `--list`, `--export`, `--compare`, `--algo`, `--py`, and `-gviz`.

## Traceability
- stakeholder need: the demo should let users select a graph by a human-friendly name instead of only numeric id
- related phase: [phase_1_1](phase_1_1.md)

## Acceptance criteria
- [Acceptance criteria](R12-G-graph-name-selection-acc-crit.md)
