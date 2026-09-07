'''yaml
title: R5-G-graph-export-compare
requirement_id: R5-G
phase: 001_001_phase
for_version: default_version
'''

# R5-G: Export graphs and compare against a database graph

The demo project SHALL provide a graph export with default
output file `out.json`, and SHALL provide `--export` and
`--compare <jsonfile>` actions that check against the graph
selected by graph ID in the database. The graph selector
SHALL be `--id`.

## Traceability
- stakeholder need: the demo should support graph export,
  graph-to-JSON comparison, and explicit graph selection by
  id
- related phase: [001_001_phase](001_001_phase.md)

## Acceptance criteria
- [Acceptance
  criteria](R5-G-graph-export-compare-acc-crit.md)
