# User Guide: Self-Learn Algorithm

The project improves itself through a repeatable 5-step learning loop, driven by the phase plans.

## Learning Loop Algorithm

| Step | Action | Referenced Plan | Output |
|------|--------|----------------|--------|
| **1. Observe** | Collect usage patterns, feedback, or gaps | [1_plan.md](plans/done/1_plan.md) (step 1-2) <br> [3_plan.md](plans/done/3_plan.md) (define vocabulary) | Noted requirements/gaps |
| **2. Extract** | Define what change addresses the gap | [5_plan.md](plans/done/5_plan.md) (step 1-2) <br> [6_plan.md](plans/done/6_plan.md) (step 1-2) | Core requirements or path candidates |
| **3. Record** | Write the change as docs or a plan | [2_plan.md](plans/done/2_plan.md) (step 1-2) <br> [4_plan.md](plans/done/4_plan.md) (if exists) | Execution record in `plans/done/` |
| **4. Verify** | Run tests, checkpoint, or review | [6_plan.md](plans/done/6_plan.md) (step 1-2) <br> [meta-trace.json](docs/meta-trace.json) | Validation output |
| **5. Reuse** | Surface the improved state for next iteration | [1_plan.md](plans/done/1_plan.md) (step 5) <br> [learning-loop.md](docs/learning-loop.md) | Index updated, phase advances |

## Phase Progression Algorithm

The project advances through phases via this algorithm:

```
phase_0.md (entry) →
phase_1.md (suggest path) →
phase_2.md (mission) →
phase_3.md (packaging/trigger)
```

Each phase:
1. Defines core requirements ([phase-requirements.md](docs/phase-requirements.md))
2. Generates challenge prompt for AI review
3. Completes review → checkpoint → phase advances

## Quick Start

1. **Observe** a gap or need (refer to [1_plan.md](plans/done/1_plan.md) for filesystem patterns)
2. **Extract** a path or requirement (use [ask](cli.md#ask) to query options if needed)
3. **Record** via the automation: `python -m self_learn refresh`
4. **Verify** with tests: `python -m self_learn test`
5. **Reuse** the improved surface for the next cycle

## Key Docs Referencing the Algorithm

- [learning-loop.md](docs/learning-loop.md) - the 5-step repeatable cycle
- [phase-requirements.md](docs/phase-requirements.md) - per-phase core requirements
- [phase-0.md](phase_0.md) - entry point and auto subproject description
- [auto-core-requi.md](docs/auto-core-requi.md) - automation submodule requirements