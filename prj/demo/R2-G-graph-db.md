'''yaml
title: R2-G-graph-db
requirement_id: R2-G
phase: phase_1_1
for_version: default_version
'''

# R2-G: Graphs stored in SQLite with graph IDs

The demo project SHALL store the graph from [R1-G](R1-G-graph.md) in a SQLite database graph structure. The database SHALL support multiple graphs using a graph ID column so each node and edge can be associated with the correct graph. Nodes SHALL belong to exactly one graph. Edges SHALL not connect nodes across different graph IDs. Missing or invalid graph IDs SHALL produce a warning.

## Traceability
- stakeholder need: the demo should persist graph data in the database, keep graph instances separable, and support graph listing
- related phase: [phase_1_1](phase_1_1.md)

## Acceptance criteria
- [Acceptance criteria](R2-G-graph-db-acc-crit.md)
