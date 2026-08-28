'''yaml
title: 001-entity-entities
purpose: Document the entities table.
version: V00.01.00
'''

# 001-entity-entities

## Table: `entities`

Stores the main things the memory knows about.

### Columns

- `id` — primary key
- `name` — unique human-readable name
- `kind` — type label, default `thing`
- `description` — optional summary text
- `created_at` — create timestamp
- `updated_at` — last change timestamp

### Use

Use one row per entity like a person, place, product, task, or concept.
