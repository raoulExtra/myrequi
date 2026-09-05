'''yaml
title: R1-G-graph
requirement_id: R1-G
phase: phase_1_1
for_version: default_version
'''

# R1-G: Graph with weighted nodes and edges

The demo project SHALL provide a graph with nodes and edges.
Nodes and edges MAY have labels. A node MAY have a text
field in the JSON source, and that text SHALL be stored in a
separate database table. Nodes and edges MAY also have
optional `color` and `style` fields in the JSON source.
These styling fields SHALL be stored as text fields with a
maximum length of 256 characters. Node weights SHALL be
scalar values and default to float weights. A node MAY also
have an integer weight. Edge weights SHALL represent abstract
meaning and SHALL default to 1 when omitted.

## Traceability
- stakeholder need: the demo should support graph-based
  structure, labels, node text in the JSON source, separate
  storage for node text, float or integer node sizing, and
  meaningful edge scoring
- related phase: [phase_1_1](phase_1_1.md)

## Acceptance criteria
- [Acceptance criteria](R1-G-graph-acc-crit.md)
