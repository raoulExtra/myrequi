---
id: 007-PLAN-HISTORY-EVIDENCE-CONSOLIDATION
category: Concrete Project Plan
project: prj/continuity_db
parent: ../../base/plans/prep/003-plan-stabilize-plans-package.md
status: active
---

# Consolidate duplicate history while retaining evidence

## End condition

Historical rows from belief, conviction, decision, and metacognitive history
sources are represented in `semantic_record_history` with their original source
identity preserved and idempotent uniqueness enforced.

Evidence and relationship tables remain distinct because they contain meaning
that is not a snapshot: conviction inputs, decision options, reasoning episodes,
concept links, provenance, and receipts. No source data is deleted.

The focused and full regression suites pass, and the implementation is
committed before `END_CONDITION_MET` is logged.
