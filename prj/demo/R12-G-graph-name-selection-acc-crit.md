'''yaml
title: R12-G-graph-name-selection-acc-crit
requirement_id: R12-G
source_requirement: R12-G-graph-name-selection.md
'''

# Acceptance criteria for R12-G

## Requirement
- [R12-G requirement](R12-G-graph-name-selection.md)

## Verification ideas
- The graph JSON may include a `name` field.
- The loader stores the JSON graph name when present.
- The graph tool accepts a `--name` option.
- The tool can resolve a graph selected by name to the correct graph ID.
- The graph name may be the stored JSON name, source-file name, or filename stem.
- `--list`, `--export`, `--compare`, `--algo`, `--py`, and `-gviz` can use `--name`.
- A reviewer can confirm name-based selection targets the intended graph.
