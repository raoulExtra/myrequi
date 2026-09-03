'''yaml
title: R1-G-graph-acc-crit
requirement_id: R1-G
source_requirement: R1-G-graph.md
'''

# Acceptance criteria for R1-G

## Requirement
- [R1-G requirement](R1-G-graph.md)

## Verification ideas
- The demo project includes a graph definition or example.
- The graph has nodes and edges.
- Each node has a scalar float weight by default.
- A node may also have an integer weight.
- A node may have a text field in the JSON source.
- That node text is stored in a separate database table.
- Each edge has a weight with default value 1 when omitted.
- A reviewer can inspect the graph and confirm the float
  weights, optional integer weights, and node text are
  represented correctly.
