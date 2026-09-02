'''yaml
title: R4-G-graph-tool-init
requirement_id: R4-G
phase: phase_1_1
for_version: default_version
'''

# R4-G: Graph tool initializes an empty SQLite graph database

The demo project SHALL provide `prj/demo/imple/V00.00.01/graph_tool.py` with an `--init` argument that creates an empty SQLite graph database ready for loading graphs. The initialization SHALL create the graph storage schema and leave it empty.

## Traceability
- stakeholder need: the demo should provide a simple tool for creating graph storage before loading data
- related phase: [phase_1_1](phase_1_1.md)

## Acceptance criteria
- [Acceptance criteria](R4-G-graph-tool-init-acc-crit.md)
