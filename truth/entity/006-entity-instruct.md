'''yaml
title: 006-entity-instruct
purpose: Document the instruct table.
version: V00.01.00
'''

# 006-entity-instruct

## Table: `instruct`

Stores queued instructions to be processed next.

### Columns

- `id` — primary key
- `content` — instruction text
- `status` — current state, usually `pending` or `done`

### Use

Use this as the pending work queue.
