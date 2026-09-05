'''yaml
title: R13-G-graph-color-style-acc-crit
requirement_id: R13-G
source_requirement: R13-G-graph-color-style.md
'''

# Acceptance criteria for R13-G

## Requirement
- [R13-G requirement](R13-G-graph-color-style.md)

## Verification ideas
- Graph JSON may include optional `color` and `style` attributes on nodes and edges.
- The loader preserves those attributes.
- The attributes are stored as text fields with a maximum length of 256 characters.
- Exported JSON includes the optional `color` and `style` fields when present.
- Graphviz DOT output includes the optional styling attributes when present.
- A reviewer can confirm the styling metadata flows from JSON to storage to export.
