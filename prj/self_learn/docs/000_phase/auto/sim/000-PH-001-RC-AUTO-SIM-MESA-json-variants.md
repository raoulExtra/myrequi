# 000-P-001-RC-AUTO-SIM-MESA-json-variants

**ID:** 000-P-001-RC-AUTO-SIM-MESA-json-variants

**Category:** Core Requirement

**Subproject:** auto/sim

**Title:** Mesa-Compatible JSON Variants for Simulations

## Description
Simulation data, model configurations, and results must be stored in Mesa-compatible JSON variants that can be loaded by Mesa's Model and Agent classes without custom deserializers, supporting phased project evolution with subprojects.

## Acceptance Criteria

### AC-001.1: JSON Schema Compatibility
- Every simulation JSON file must be loadable via `Model.from_json(json_string)`
- Agent states must support `Agent.from_dict(dict)` for JSON deserialization
- Schema follows Mesa's CellAgent and Model conventions with `__class__` key

### AC-001.3: JSON Schema Structure: JSON Schema Structure
Model variants must include:
```json
{
  "__class__": "prj.self_learn.auto.sim.models.PhasedProjectModel",
  "phases": [...],
  "subprojects": [...],
  "requirements": [...]
}
```

### AC-001.4: Mesa Integration
- `Model.to_json()` produces valid JSON for `Model.from_json()`
- `Agent.to_dict()` produces valid dict for `Agent.from_dict()`
- Round-trip preserves numeric types (int vs float)
- Works with Mesa 3.5.1 installed in `.venv/`

## Status
draft

## Related
- CR5: Learning Domain Separation
- auto/sim README