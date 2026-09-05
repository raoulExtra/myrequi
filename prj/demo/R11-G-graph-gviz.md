'''yaml
title: R11-G-graph-gviz
requirement_id: R11-G
phase: phase_1_1
for_version: default_version
'''

# R11-G: Graph tool can export Graphviz DOT and SVG

The demo project SHALL provide a graph-tool `-gviz` mode that writes a Graphviz DOT file for the selected graph and then produces an SVG rendering from that DOT file. By default, the export SHALL be stored under `assets/graph.dot` and `assets/graph.svg`. The Graphviz export SHALL use the graph selected by `--id` or `--name`.

## Traceability
- stakeholder need: the demo should visualize graphs as DOT and SVG for inspection and sharing
- related phase: [phase_1_1](phase_1_1.md)

## Acceptance criteria
- [Acceptance criteria](R11-G-graph-gviz-acc-crit.md)
