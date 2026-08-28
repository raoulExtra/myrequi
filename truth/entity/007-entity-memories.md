'''yaml
title: 007-entity-memories
purpose: Document the memories table.
version: V00.01.00
'''

# 007-entity-memories

## Table: `memories`

Stores indexed memory records for rich retrieval.

### Columns

- `id` — primary key
- `slug` — unique memory identifier
- `kind` — memory type, like `historical_snapshot`
- `timestamp` — memory time marker
- `scope` — covered domain or context
- `confidence` — confidence label
- `importance` — priority label
- `summary` — short summary text
- `observation` — observed statement block
- `unknown` — uncertainty block
- `principle` — guiding principle block
- `message_to_future_reader` — note to later readers
- `source_path` — source file path
- `raw_text` — full original text
- `created_at` — create timestamp
- `updated_at` — last change timestamp

### Use

Use this table as the main index for full memory records.
