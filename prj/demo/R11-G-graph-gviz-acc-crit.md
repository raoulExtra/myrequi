'''yaml
title: R11-G-graph-gviz-acc-crit
requirement_id: R11-G
source_requirement: R11-G-graph-gviz.md
'''

# Acceptance criteria for R11-G

## Requirement
- [R11-G requirement](R11-G-graph-gviz.md)

## Verification ideas
- The graph tool accepts a `-gviz` option.
- The tool uses the graph selected by `--id` or `--name`.
- Running `-gviz` creates a DOT file under `assets/graph.dot` by default.
- Running `-gviz` also creates an SVG file under `assets/graph.svg` by default.
- A reviewer can confirm the DOT and SVG outputs were produced from the selected graph.
