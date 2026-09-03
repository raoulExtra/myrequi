'''yaml
title: R2-G-graph-db-acc-crit
requirement_id: R2-G
source_requirement: R2-G-graph-db.md
'''

# Acceptance criteria for R2-G

## Requirement
- [R2-G requirement](R2-G-graph-db.md)

## Verification ideas
- The demo project includes a SQLite-backed graph storage
  design.
- The graph from R1-G can be stored in the database.
- The database supports multiple graphs.
- Each graph has a graph ID column.
- Nodes store or reference exactly one graph ID.
- Edges store or reference a graph ID and do not cross graph
  boundaries.
- Missing or invalid graph IDs produce a warning.
- A reviewer can confirm graph membership is unambiguous for
  both nodes and edges.
