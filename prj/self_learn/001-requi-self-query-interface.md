# Requirement: Self-query interface

## Overview
A Python module `self_query.py` that enables the cognition.db system to query its own memory and state for self-improvement purposes.

## Rationale
The system needs to be able to:
1. Recall relevant past observations and decisions
2. Query its current goal and focus state
3. Find related plans and work items
4. Store new learnings and insights

## Detailed specification
- Module name: `self_query.py`
- Location: `imple/V00_00_01/self_query.py`
- Dependencies: `continuity.db`, `memory_command.py`, `plan_command.py`
- Primary function: `query_self(query, db_path='continuity.db')` 
- Should return structured JSON with recall results

## Success criteria
- Can recall relevant past notes
- Can answer using prior context instead of starting over
- New conclusions are written back with traceable provenance