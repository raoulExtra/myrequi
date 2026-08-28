'''yaml
title: 004-entity-events
purpose: Document the events and event_entities tables.
version: V00.01.00
'''

# 004-entity-events

## Table: `events`

Stores time-based actions or occurrences.

### Columns

- `id` — primary key
- `name` — event name
- `happened_at` — event time
- `summary` — short description
- `payload_json` — full event payload

## Table: `event_entities`

Connects events to entities.

### Columns

- `event_id` — linked event
- `entity_id` — linked entity
- `role` — why the entity belongs to the event, default `related`

### Use

Use events when time and sequence matter, like:
- user asked a question
- system updated a fact
- agent answered
