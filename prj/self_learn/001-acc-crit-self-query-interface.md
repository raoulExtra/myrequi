# Acceptance Criteria: Self-query interface

## R1.1: Module exists and imports
- [ ] File exists at `imple/V00_00_01/self_query.py`
- [ ] Module can be imported without errors

## R1.2: Database connection
- [ ] Can connect to continuity.db
- [ ] Can connect to thinker/thinker.db (optional)
- [ ] Graceful error handling for missing database

## R1.3: Recall functionality
- [ ] Query returns structured JSON
- [ ] Results include relevance scores
- [ ] Results include source provenance

## R1.4: Metacognitive state access
- [ ] Can query primary_goal
- [ ] Can query current_focus
- [ ] Can query current_aspect

## R1.5: Plan recall
- [ ] Can list active work plans
- [ ] Can list plan steps with status

## R1.6: Integration test
- [ ] Query returns expected data structure
- [ ] Can run: `python imple/V00_00_01/self_query.py "status"`