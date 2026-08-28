'''yaml
title: 005-entity-variables
purpose: Document the variables table.
version: V00.01.00
'''

# 005-entity-variables

## Table: `variables`

Stores small named values.

### Columns

- `name` — unique key
- `value` — stored text value

### Use

Use for simple config and shared state, like:
- `fe=true`
- `glob.country=Germany`
