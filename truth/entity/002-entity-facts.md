'''yaml
title: 002-entity-facts
purpose: Document the facts table.
version: V00.01.00
'''

# 002-entity-facts

## Table: `facts`

Stores key/value facts attached to an entity.

### Columns

- `id` — primary key
- `entity_id` — linked entity
- `key` — fact name, like `capital` or `status`
- `value` — fact value
- `scope` — context label, default `general`
- `source` — optional origin text or URL
- `created_at` — create timestamp
- `updated_at` — last change timestamp

### Use

Use for simple assertions like:
- `Germany -> capital = Berlin`
- `Project X -> status = active`
