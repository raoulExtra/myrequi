# 000-P-004-RC-Embedded-Learning-Loop

**ID:** 000-P-004-RC

**Category:** Core Requirement

**Title:** Embedded Learning Loop

## Description
A complete learning loop (Observe → Update → Verify → Reuse) must be embedded in project tooling and integrated with self_query.py and pi_query.py for continuous improvement cycles.

## Acceptance Criteria

### AC-004.1: Observe Phase
- Memory queries use `self_query.py` for context retrieval
- Query results include relevant goals, focus, and context
- Observation results are stored with traceability metadata

### AC-004.2: Update Phase
- Changes are applied via `pi` commands or `pi_query.py`
- Updates modify filesystem, database, or code as needed
- Each update has an operator and justification field

### AC-004.3: Verify Phase
- Before/after states are compared with measurable metrics
- Verification includes automated test passes
- Success criteria are defined for each improvement

### AC-004.4: Reuse Phase
- Patterns are stored in `reasoning_episodes` table
- JSON patterns are saved to `knowledge/patterns/`
- Stored patterns can be retrieved and applied to new tasks

## Status
draft

## Related
- Phase 0: Core infrastructure requirements
