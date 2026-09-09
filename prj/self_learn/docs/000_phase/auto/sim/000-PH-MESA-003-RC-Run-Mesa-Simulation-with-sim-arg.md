# 000-P-MESA-003-RC-Run-Mesa-Simulation-with-sim-arg

**ID:** 000-P-MESA-003-RC

**Category:** Core Requirement

**Subproject:** auto/sim

**Title:** Run Mesa Simulations with -sim JSON Argument

## Description
Python code in `prj/self_learn/imple/V00_00_01/auto/sim/` must support running Mesa simulations using a `-sim <json>` command-line argument, enabling specification of variant JSON files to control simulation execution. The `-sim` argument is designated for the `prj_handler.py` module.

## Acceptance Criteria

### AC-001.1: Python Module for Simulation Runner
- Create `prj/self_learn/imple/V00_00_01/auto/sim/run_simulation.py` module
- Module must accept `-sim <path>` or `--sim <path>` argument for JSON variant file
- Module provides `run_simulation(json_path)` function or equivalent CLI entry point

### AC-001.2: JSON Variant Loading
- JSON file specified via `-sim` argument must be loadable from the project's JSON directory
- JSON must follow Mesa-compatible variant format with `__class__` key
- Module returns proper Mesa Model and Agent objects from loaded JSON

### AC-001.3: Command-Line Interface Integration (prj_handler.py)
- `prj_handler.py` must support `-sim <json>` argument to run simulation directly
- Alternative: standalone script `run_mesa_sim.py` in `auto/sim/` that accepts `-sim <json>`
- Output includes iteration metrics, final state, and trace ID

### AC-001.4: Execution Workflow
- Loaded model executes learning loop (Observe → Update → Verify → Reuse)
- Each simulation step logs to console with ISO 8601 timestamps
- Results stored in `.pi/tasks/` with trace IDs from variant metadata
- Tool exits with appropriate exit code (0 for success, non-zero for failure)

### AC-001.5: Error Handling
- Invalid JSON files produce clear error messages with traceback
- Missing `-sim` argument shows usage help
- Non-existent file paths are handled gracefully
- Model instantiation errors reported with context from JSON variant

### AC-001.6: Integration with Existing Infrastructure
- Works with existing JSON directory structure
- Compatible with Mesa 3.5.1 installed in project `.venv/`
- State changes recorded to `metacognitive_state.json`
- Patterns saved to `knowledge/patterns/` when applicable

## Related Requirements

- **000-P-MESA-004-RC-sim-arg-for-prj-handler.md** - Clarifies -sim argument is for prj_handler.py, NOT pi_query.py
- **000-P-MESA-001-RC-Mesa-Simulation-Variants**
- **000-P-MESA-002-RC-Run-Mesa-Simulations-from-JSON**
- CR4: Embedded Learning Loop
- CR5: Learning Domain Separation

## Validation Commands
```bash
# Run simulation with JSON from project directory (via prj_handler)
source .venv/bin/activate
python3 prj_handler.py -sim self_learn_evolution.json

# Standalone script
python3 run_mesa_sim.py --sim self_learn_evolution.json

# pi_query.py does NOT accept -sim (per 000-P-MESA-004-RC)
python3 pi_query.py --help  # Should not show -sim option
```

## Status
draft