---
id: 004-PLAN-SEPARATE-SEMANTIC-LAYERS
category: Concrete Project Plan
project: prj/continuity_db
parent: ../../base/plans/prep/003-plan-stabilize-plans-package.md
status: active
---

# Separate semantic layers without destructive table collapse

## Problem

`beliefs`, `convictions`, `metacognitive_state`, `identity`, `decisions`, and
`concepts` currently overlap. `v_core_model` acknowledges the collapse but does
not provide enforceable ownership boundaries.

## Chosen solution

Do not merge or delete the existing tables. Give each store one canonical
semantic role and expose a normalized read model:

| Store | Canonical role | Must not become |
|---|---|---|
| `concepts` | vocabulary, categories, and definitions | a claim or runtime state |
| `beliefs` | propositions held with evidence/confidence and revision | a definition, policy, or decision record |
| `convictions` | durable endorsed principles that guide judgment | a duplicate belief; link to source beliefs |
| `metacognitive_state` | mutable engine policy, attention, capability, and self-model state | identity facts or ordinary world claims |
| `identity` | stable identity commitments and continuity rules | transient metacognitive state |
| `decisions` | choices made, alternatives, rationale, and status | beliefs or definitions |

Overlap is allowed only when records have different roles and an explicit
provenance or semantic link explains the relationship.

## End condition

The plan ends only after `END_CONDITION_MET` is recorded when all of these are
true:

1. A versioned semantic ownership contract exists in the repository and DB.
2. `v_core_model` describes the six roles above and no longer calls beliefs and
   convictions the only collapsed concepts.
3. A normalized read view exposes each record as `semantic_type`, `semantic_key`,
   `statement`, `confidence`, `status`, and `source_table`.
4. A deterministic overlap report identifies exact/near duplicate statements
   without deleting data.
5. Existing overlapping examples are classified as `definition`, `claim`,
   `principle`, `policy_state`, `identity_rule`, or `decision`, with explicit
   links where more than one record is intentionally retained.
6. Tests prove that new records cannot silently cross semantic boundaries and
   that the migration is idempotent and reversible.
7. Full relevant regression tests pass, and the final repository state is
   committed.

## Non-goals

- Do not delete or automatically merge existing records.
- Do not claim that semantic similarity proves identity.
- Do not store hidden chain-of-thought.
- Do not change SQLite `user_version` unless a separately reviewed migration
  policy authorizes it.

## Ordered parts

1. `004/00-contract-and-inventory.md`
2. `004/01-normalized-read-model.md`
3. `004/02-overlap-classification.md`
4. `004/03-integrity-and-links.md`
5. `004/04-regression-and-closeout.md`

The final logfile protocol is inherited from plan 003: record
`END_CONDITION_MET`, perform final status checks, then move active logs to
`done/` as the last filesystem action.
