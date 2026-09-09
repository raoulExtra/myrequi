# Requirement: Filesystem-based metacognitive state

## Overview
Implement filesystem-based storage for metacognitive_state entries (primary_goal, current_focus, current_aspect, etc.) as JSON files instead of storing them in continuity.db.

## Rationale
The self_learn project should store persistent project state in version-controlled filesystem files rather than the continuity.db database. This ensures:
- Project state is auditable and visible in git history
- State can be easily inspected and modified without database access
- Changes to goals/focus are directly traceable in version control
- Simpler backup and restore through filesystem operations

## Detailed specification
- Module: `self_query.py` should check `metacognitive_state.json` first
- Location: `prj/self_learn/metacognitive_state.json`
- Schema: `{ "migrated_from": "...", "entries": { "state_key": { "value", "category", ... } } }`
- Fallback: If JSON file missing, query continuity.db
- Update helper: `update_metacognitive_state.py` for filesystem modifications
- All reads/writes through the same unified interface

## Success criteria
- [ ] self_query.py reads from JSON file when it exists
- [ ] JSON entries match continuity.db format (state_key, value, category, etc.)
- [ ] update_metacognitive_state.py can add/update entries
- [ ] pi_query.py status shows updated values from JSON
- [ ] Backup/restore works via normal file operations
- [ ] git can see changes to metacognitive_state.json