'''yaml
title: 009-entity-memory-links
purpose: Document the memory_links table.
version: V00.01.00
'''

# 009-entity-memory-links

## Table: `memory_links`

Stores links extracted from memory text.

### Columns

- `id` — primary key
- `memory_id` — linked memory
- `from_name` — source node name
- `via_name` — optional intermediate node or context
- `relation` — relation label
- `to_name` — target node name
- `arrow` — link style, like `->` or `<->`
- `raw_line` — original link text

### Use

Use this table for graph-style retrieval and relationship browsing.
