# 000-P-MESA-004-RC-sim-arg-for-prj-handler

**ID:** 000-P-MESA-004-RC

**Category:** Core Requirement

**Subproject:** auto/sim

**Title:** -sim Argument for prj_handler.py, Not pi_query.py

## Description
The `-sim <json>` command-line argument is designated for the new `prj_handler.py` module, not for `pi_query.py`. This clarification ensures proper separation of concerns between the project handler and the Pi query interface.

## Acceptance Criteria

### AC-001.1: prj_handler.py Module
- Create `prj/self_learn/imple/V00_00_01/auto/sim/prj_handler.py` module
- Module must accept `-sim <path>` or `--sim <path>` argument for JSON variant file
- Module provides dedicated simulation handling distinct from Pi query interface

### AC-001.2: pi_query.py Exclusion
- `pi_query.py` must NOT accept `-sim <json>` argument
- `pi_query.py` continues to support its existing query functionality
- No `-sim` related code in `pi_query.py` implementation

### AC-001.3: Argument Routing
- `-sim <json>` routes to `prj_handler.py` simulation execution
- Alternative arguments (e.g., `-p`, `--prompt`) in `pi_query.py` handle Pi interactions
- Clear separation of CLI argument namespaces

### AC-001.4: Documentation
- Requirement file documents the `-sim` argument scope
- Related requirement `000-P-MESA-003-RC-Run-Mesa-Simulation-with-sim-arg.md` references this constraint
- Project contributors understand `-sim` is prj_handler-specific

### AC-001.5: Integration
- `prj_handler.py` integrates with existing JSON directory structure
- Results from `prj_handler.py -sim` follow same output format as `000-P-MESA-003-RC`
- Compatible with Mesa 3.5.1 installed in project `.venv/`

## Related Requirements

- **000-P-MESA-003-RC-Run-Mesa-Simulation-with-sim-arg.md** - Core requirement for Mesa simulation runner (references this constraint)
- **000-P-MESA-002-RC-Run-Mesa-Simulations-from-JSON.md** - Earlier requirement on JSON variant execution
- **000-P-001-RC-AUTO-SIM-MESA-json-variants.md** - Acceptance criteria for JSON variants

## CLI Usage Examples

### prj_handler.py (ACCEPT -sim)
```bash
python3 prj_handler.py -sim test_model.json
python3 prj_handler.py --sim test_model.json --iterations 200
```

### pi_query.py (DO NOT USE -sim)
```bash
# These should NOT use -sim argument:
python3 pi_query.py "what do you know"
python3 pi_query.py --prompt "reflect on this project"
# -sim is NOT a valid argument for pi_query.py
```

## Validation Commands
```bash
# Test prj_handler.py accepts -sim
source .venv/bin/activate
python3 prj_handler.py -sim self_learn_evolution.json

# Test pi_query.py rejects -sim (or ignores it gracefully)
python3 pi_query.py --help  # Should not show -sim option
```

## Status
draft

## Revision History
- **V00_00_01** - Initial draft clarifying -sim argument scope separation