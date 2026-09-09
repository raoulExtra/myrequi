# 000-P-002-RC-Filesystem-State-Management

**ID:** 000-P-002-RC

**Category:** Core Requirement

**Title:** Filesystem State Management

## Description
Metacognitive state must be stored in a git-versioned JSON file with proper timestamps and accessible state keys, separate from the continuity.db database.

## Acceptance Criteria

### AC-002.1: Git Version Control
- `metacognitive_state.json` is tracked by git
- Changes to the file are visible in git history
- The file location is documented at `prj/self_learn/metacognitive_state.json`

### AC-002.2: Timestamp Format
- All state changes include ISO 8601 formatted timestamps
- Timestamps are in the format: `YYYY-MM-DDTHH:MM:SS.ffffff`
- `created_at` and `completed_at` fields follow this format

### AC-002.3: Migratable State Keys
- At least 5 state keys are supported: primary_goal, current_focus, current_aspect, active_project, current_project
- Each key can be read and updated independently
- Missing keys fall back to database values

### AC-002.4: Query Interface
- State is readable via `self_query.py status`
- State updates work via `update_metacognitive_state.py`
- The interface returns JSON with consistent schema

## Status
draft

## Related
- Phase 0: Core infrastructure requirements