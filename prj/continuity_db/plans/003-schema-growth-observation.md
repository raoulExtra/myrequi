---
id: 003-SCHEMA-GROWTH-OBSERVATION
category: Concrete Project Plan
parent: ../../base/plans/prep/003-plan-stabilize-plans-package.md
project: prj/continuity_db
status: active
---

# Observe schema growth without data-explosion assumptions

## Task

Measure and document the continuity database's structural growth over a
5-day interval, while preserving the observation that a large schema can
coexist with controlled data growth. This plan must not claim causation from
counts alone.

## End condition

`END_CONDITION_MET` only when, after five days, repository evidence records:

- 123 tables;
- 64 views;
- 80 triggers; and
- SQLite schema version `0`.

The evidence must include the exact query, timestamp, database identity/hash,
and a comparison with the baseline. Any count change must be explained or the
end condition remains unmet.

## Concrete project details

- Project root: `/home/peter/xmyrequi/myrequi`
- Database: `continuity.db`
- Plan package: `prj/continuity_db/plans`
- Test/verification language: Python 3
- Baseline command: the `sqlite3` query in Step 1.2
- No schema or application mutation is authorized by this observation plan.

## Steps

### Step 1: Capture baseline

Record UTC timestamp, database file size, SHA-256 hash, SQLite version, and the
following query output:

```sql
SELECT type, COUNT(*)
FROM sqlite_master
WHERE type IN ('table', 'view', 'trigger')
  AND name NOT LIKE 'sqlite_%'
GROUP BY type
ORDER BY type;

PRAGMA user_version;
```

Current baseline captured during plan creation:

```text
tables=123
views=64
triggers=80
schema_version=0
```

### Step 2: Inventory and guard the observation

Create a deterministic inventory of object names and SQL definitions. Verify
that the observation scripts do not write to `continuity.db`. Add a focused test
for the count query and schema-version readout if a project test location is
available.

### Step 3: Wait five days

Do not alter the database for this plan. Record the planned follow-up timestamp
as baseline timestamp plus 5 days. Existing unrelated work must be noted rather
than silently attributed to this plan.

### Step 4: Capture follow-up

Repeat the exact baseline query and metadata capture. Compare counts, names,
definitions, file hash, and timestamps. Explain every difference.

### Step 5: Conclude

If all end-condition values and evidence match, append `END_CONDITION_MET` to
the project execution log, perform the final status check, and apply the
terminal logfile protocol from the reusable plan. If not, record the discrepancy
and leave the plan active.

## Non-goals

- Do not delete, consolidate, or rename database objects.
- Do not change `PRAGMA user_version`.
- Do not infer that schema size alone proves or disproves data explosion.
- Do not store raw database contents in the observation record.
