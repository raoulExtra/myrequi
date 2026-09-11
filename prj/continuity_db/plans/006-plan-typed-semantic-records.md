---
id: 006-PLAN-TYPED-SEMANTIC-RECORDS
category: Concrete Project Plan
project: prj/continuity_db
parent: ../../base/plans/prep/003-plan-stabilize-plans-package.md
status: active
---

# Add typed semantic details and immutable history

## End condition

`END_CONDITION_MET` only after these three structures are implemented and
validated:

- `semantic_records`: one canonical current record per semantic item;
- `semantic_record_details`: optional, type-constrained details;
- `semantic_record_history`: immutable snapshots and audit events.

The implementation must preserve existing data, use explicit typed columns and
constraints rather than an untyped JSON bag, be idempotent, and pass the full
regression suite.
