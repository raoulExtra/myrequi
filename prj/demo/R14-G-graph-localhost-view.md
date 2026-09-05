'''yaml
title: R14-G-graph-localhost-view
requirement_id: R14-G
phase: phase_1_1
for_version: default_version
'''

# R14-G: Graph tool can serve a selected graph on localhost

The demo project SHALL provide a small localhost provider that serves the selected graph as SVG over HTTP. The provider SHALL use the graph selected by `--id` or `--name`, and the root page SHALL display the rendered graph for easy local viewing.

## Traceability
- stakeholder need: the demo should show the graph in a browser on localhost without manual file handling
- related phase: [phase_1_1](phase_1_1.md)

## Acceptance criteria
- [Acceptance criteria](R14-G-graph-localhost-view-acc-crit.md)
