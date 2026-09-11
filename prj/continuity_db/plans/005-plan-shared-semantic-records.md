---
id: 005-PLAN-SHARED-SEMANTIC-RECORDS
category: Concrete Project Plan
project: prj/continuity_db
parent: ../../base/plans/prep/003-plan-stabilize-plans-package.md
status: active
---

# Consolidate common semantic storage

## End condition

`END_CONDITION_MET` only after a shared `semantic_records` table exists and
supports exactly these semantic families:

- Knowledge: `concept`, `belief`, `conviction`
- Self and policy: `identity`, `metacognitive_state`
- Action: `decision`

The table must contain common fields for semantic key, statement, confidence,
status, provenance, version, source identity, and timestamps. Existing data must
be represented without loss, existing consumers must continue to work through
compatibility views or synchronization triggers, migration must be idempotent,
and focused plus full regression tests must pass.

## Safety rule

Do not drop or rewrite the existing source tables in this plan. They remain
compatibility surfaces until a later, separately approved removal plan. The
shared table becomes the canonical common-field projection first.

## Steps

1. Write failing tests for schema, six semantic types, row preservation, and
   rerunnable migration.
2. Create and backfill `semantic_records` with explicit source identity.
3. Add synchronization for source inserts, updates, and deletes.
4. Make `v_semantic_records` read from the shared table and preserve its public
   columns.
5. Run focused and full regressions, verify counts and foreign keys, and commit.
6. Record `END_CONDITION_MET`; move active logs to `done/` as the final action.
