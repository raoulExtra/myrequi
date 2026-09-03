'''yaml
title: R9-G-graph-to-py-ast
requirement_id: R9-G
phase: phase_1_1
for_version: default_version
'''

# R9-G: Convert a selected graph into a Python AST

The demo project SHALL provide a graph-to-Python-AST conversion path
for the selected graph. The conversion SHALL be primarily a traversal
plus node-construction process, mapping graph structure into Python
`ast` nodes. The selected input SHALL use a special JSON form designed
for AST generation, with explicit node types, ordered child lists, and
field values that map cleanly to Python `ast` nodes. The examples
folder SHALL also include graph-syntax counterpart JSON files that
represent the same structures as node-and-edge graphs.

## Traceability
- stakeholder need: the demo should be able to turn a graph into a Python AST using graph traversal and AST node construction
- related phase: [phase_1_1](phase_1_1.md)

## Acceptance criteria
- [Acceptance criteria](R9-G-graph-to-py-ast-acc-crit.md)
