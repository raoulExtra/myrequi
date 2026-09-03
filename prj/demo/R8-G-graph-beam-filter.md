'''yaml
title: R8-G-graph-beam-filter
requirement_id: R8-G
phase: phase_1_1
for_version: default_version
'''

# R8-G: Beam search with filtering

The demo project SHALL provide a beam-search algorithm on the selected graph, and SHALL apply filtering during expansion or re-ranking. Beam search SHALL keep a limited set of the most promising paths at each step, instead of exploring every path.

## Traceability
- stakeholder need: the demo should support a graph search method suitable for repeated thinking paths
- related phase: [phase_1_1](phase_1_1.md)

## Acceptance criteria
- [Acceptance criteria](R8-G-graph-beam-filter-acc-crit.md)
