'''yaml
title: R6-G-graph-algo
requirement_id: R6-G
phase: phase_1_1
for_version: default_version
'''

# R6-G: Run an algorithm on a selected graph

The demo project SHALL provide an `--algo` argument, such as
`A*`, that runs an algorithm on the graph selected with
`--id`. The algorithm SHALL accept a start node argument and
MAY accept an optional goal node argument.

## Traceability
- stakeholder need: the demo should support algorithm
  execution on a selected graph with configurable start and
  optional goal nodes
- related phase: [phase_1_1](phase_1_1.md)

## Acceptance criteria
- [Acceptance criteria](R6-G-graph-algo-acc-crit.md)
