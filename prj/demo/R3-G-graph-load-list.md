'''yaml
title: R3-G-graph-load-list
requirement_id: R3-G
phase: phase_1_1
for_version: default_version
'''

# R3-G: Load and list graphs from simple JSON

The demo project SHALL provide `--load` and a solo `--list` action for graph storage. The tool SHALL also accept an `--id` argument for graph selection. The loader SHALL be able to load a graph from a simple JSON file such as `001-graph.json`, and SHALL be able to list loaded graphs. The loader SHALL use the file name to determine the graph ID, so `001-graph.json` loads as graph ID `1`. If graph ID `1` already exists in the database, the loader SHALL delete existing rows for that graph ID before inserting the new graph. The JSON format SHALL be the simplest format that satisfies [R1-G](R1-G-graph.md), including node text in the JSON source. The JSON source SHALL not store `graph_id`; the database records the graph ID on load. If an edge references a missing node, the loader SHALL show a warning.

## Traceability
- stakeholder need: the demo should support simple graph import, graph listing, graph selection by id, import-time validation warnings, and replace-on-load behavior
- related phase: [phase_1_1](phase_1_1.md)

## Acceptance criteria
- [Acceptance criteria](R3-G-graph-load-list-acc-crit.md)
