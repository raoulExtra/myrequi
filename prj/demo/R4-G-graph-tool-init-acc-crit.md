'''yaml
title: R4-G-graph-tool-init-acc-crit
requirement_id: R4-G
source_requirement: R4-G-graph-tool-init.md
'''

# Acceptance criteria for R4-G

## Requirement
- [R4-G requirement](R4-G-graph-tool-init.md)

## Verification ideas
- `prj/demo/imple/V00.00.01/graph_tool.py` exists.
- The tool accepts an `--init` argument.
- Running `--init` creates an SQLite database file.
- The database contains the graph storage schema.
- The database is empty of graph rows after initialization.
- A reviewer can confirm the database was created
  successfully.
