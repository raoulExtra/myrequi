# Acceptance Criteria: Filesystem-based metacognitive state

## R4: Filesystem-based metacognitive state

### AC1: JSON file exists in correct location
**Given** the self_learn project is configured
**When** checking the project directory
**Then** a `metacognitive_state.json` file exists in `prj/self_learn/`

### AC2: JSON file has correct schema
**Given** a valid metacognitive_state.json file
**When** loading it with `self_query.load_metacognitive_state_from_json()`
**Then** it returns a dict with `entries` key containing state entries
**And** each entry has `value`, `category`, `updated_at` fields

### AC3: self_query.py reads from JSON first
**Given** both metacognitive_state.json and continuity.db have entries
**When** querying for primary_goal
**Then** the value from JSON file is returned (not database)

### AC4: update_metacognitive_state.py updates JSON correctly
**Given** the update helper is available
**When** calling with `update_metacognitive_state.py "test" "value"`
**Then** the JSON file is updated with new entry
**And** the entry has current timestamp

### AC5: pi_query.py status shows JSON values
**Given** metacognitive_state.json has current_goal entry
**When** running `pi_query.py --status`
**Then** the terminal shows the JSON value

### AC6: JSON file is git-trackable
**Given** metacognitive_state.json exists
**When** making changes to the file
**Then** git diff shows the changes
**And** git log can trace history of modifications