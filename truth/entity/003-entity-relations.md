'''yaml
title: 003-entity-relations
purpose: Document the relations table.
version: V00.01.00
'''

# 003-entity-relations

## Table: `relations`

Stores links between two entities.

### Columns

- `id` — primary key
- `from_entity_id` — source entity
- `relation` — relation name, like `part_of` or `owns`
- `to_entity_id` — target entity
- `weight` — strength or confidence, default `1.0`
- `source` — optional origin text or URL
- `created_at` — create timestamp

### Use

Use for graph-like memory:
- `Berlin part_of Germany`
- `Alice owns Laptop`
