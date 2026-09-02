'''yaml
title: R5-G-graph-export-compare-acc-crit
requirement_id: R5-G
source_requirement: R5-G-graph-export-compare.md
'''

# Acceptance criteria for R5-G

## Requirement
- [R5-G requirement](R5-G-graph-export-compare.md)

## Verification ideas
- The demo project can export a graph to a default file named `out.json`.
- The demo project supports `--export` and `--compare <jsonfile>` actions.
- The compare action checks the JSON file against a graph selected by graph ID in the database.
- The graph selector is `--id`.
- A reviewer can confirm the export file name and compare behavior are correct.
