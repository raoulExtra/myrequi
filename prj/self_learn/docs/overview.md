# Self-Learn Project Overview

## Purpose
This project implements the self-improvement infrastructure for cognition.db, enabling the system to systematically improve its own reasoning, planning, and learning capabilities.

## The Learning Loop
The core of self-improvement follows the cycle:

1. **Observe** — Query memory for relevant context and identify gaps
2. **Update** — Make targeted changes to policies, code, or memory
3. **Verify** — Check that changes achieved the intended improvement
4. **Reuse** — Store patterns for future self-improvement cycles

## Key Components

### Self-Query Interface (`self_query.py`)
Enables the system to query its own memory:
- Metacognitive state (goals, focus, aspect)
- Active work plans and steps
- Open questions and blockers
- Recent reasoning episodes

### Plan Generation (`gen_improv_plan.py`)
Generates numbered markdown plan files from:
- Database work plans
- Prompt-based inputs
- Linked plan relationships

### Learning Loop (`run_learning_cycle()`)
Automates the observe → update → verify → reuse cycle with:
- Audit trail in reasoning_episodes
- Before/after comparison
- Pattern storage for reuse

## Project Structure

```
prj/self_learn/
├── 000_phase.md           # Entry point
├── 001_phase.md           # Core implementation
├── rules/               # Governance rules
├── imple/
│   └── V00_00_01/
│       ├── self_query.py      # Memory query interface
│       └── gen_improv_plan.py # Plan generation
├── docs/
│   └── overview.md          # This file
├── tests/                   # Tests for implementation
└── plans/                   # Work plans and executions
```

## Getting Started

1. Set the primary goal:
   ```bash
   python project_command.py "project goal set self_learn Create self-improving infrastructure for cognition.db"
   ```

2. Query current state:
   ```bash
   python imple/V00_00_01/self_query.py status
   ```

3. Generate a plan:
   ```bash
   python plans/gen_plan.py --plan-key self_improve_memory_system
   ```

## Integration with Continuity.db

All self-improvement work is stored in continuity.db:
- `metacognitive_state` — Goals and focus
- `work_plans` — Work items
- `work_plan_steps` — Actionable steps
- `reasoning_episodes` — Audit trail
- `journal` — Notes and reflections

## Vision
The self-learn project enables cognition.db to become a "thinking partner" that:
- Remembers past reasoning
- Applies learned patterns
- Improves its own structure
- Maintains coherent long-term reasoning

## Note
qwen/qwen3-coder-30b-a3b-instruct