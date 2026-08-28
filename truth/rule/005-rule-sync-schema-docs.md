'''yaml
title: 005-rule-sync-schema-docs
purpose: Keep sqlite schema changes reflected in truth/entity documentation.
version: V00.01.00
'''

# 005-rule-sync-schema-docs

Whenever the sqlite schema changes or new tables/columns are added, update the matching docs under `truth/entity/` in the same change.

## Rule

- Add or update one numbered `.md` file per table or related table group.
- Document columns, purpose, and intended use.
- Keep the index file in sync with the current sqlite tables.
- If a new memory structure is added, document how to retrieve it.
