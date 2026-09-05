'''yaml
title: R3-G-graph-load-list-acc-crit
requirement_id: R3-G
source_requirement: R3-G-graph-load-list.md
'''

# Acceptance criteria for R3-G

## Requirement
- [R3-G requirement](R3-G-graph-load-list.md)

## Verification ideas
- The demo project can load a graph from a simple JSON file.
- The loader supports `--load`, a solo `--list` action, and
  an `--id` argument.
- A file named `001-graph.json` loads as graph ID `1`.
- Loading graph ID `1` replaces any existing rows for graph
  ID `1` before inserting the new graph.
- The JSON format is simple and sufficient for R1-G nodes,
  edges, node text, optional graph name, and optional
  node/edge color and style.
- The JSON source does not need to store `graph_id`.
- The database stores graph ID during load.
- If provided, the JSON graph name is stored for later
  name-based selection.
- If provided, node and edge color/style attributes are
  preserved.
- If an edge references a missing node, the loader shows a
  warning.
- The demo project can list loaded graphs.
- A reviewer can confirm the loaded graph ID, optional graph
  name, styling attributes, and list output are correct.
