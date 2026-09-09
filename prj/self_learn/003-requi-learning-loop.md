# Requirement: Learning loop automation

## Overview
Implement the systematic learning loop: Observe → Update → Verify → Reuse for self-improvement cycles.

## Rationale
The cognition.db system needs a standardized process for:
1. Observing current state and performance
2. Identifying gaps and opportunities
3. Making targeted updates to policies or code
4. Verifying improvements are effective
5. Reusing patterns for future improvements

## Detailed specification
- Loop function: `run_learning_cycle()` in self_query.py
- Observe phase: query memory for relevant context
- Update phase: propose and apply changes
- Verify phase: check if change achieved goal
- Reuse phase: store pattern for future reference
- Integration with reasoning_episodes table for audit trail

## Success criteria
- Can run a complete learning cycle
- Each phase produces audit trace
- Results can be compared before/after
- Patterns can be stored for reuse