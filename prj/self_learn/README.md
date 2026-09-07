# Self-Learn Project

A self-improvement infrastructure for cognition.db that enables systematic learning cycles.

## Overview

This project implements tools for the cognition.db system to improve its own reasoning, planning, and learning capabilities through a structured process:

1. **Observe** — Query memory for relevant context and identify gaps
2. **Update** — Make targeted changes to policies, code, or memory  
3. **Verify** — Check that changes achieved the intended improvement
4. **Reuse** — Store patterns for future self-improvement cycles

## Core Components

### self_query.py
Memory-assisted query interface for self-improvement work.

Usage:
```bash
python imple/V00_00_01/self_query.py status    # Show current state
python imple/V00_00_01/self_query.py goal      # Show primary goal
python imple/V00_00_01/self_query.py plans     # List active plans
python imple/V00_00_01/self_query.py "recall"  # General memory recall
```

### gen_improv_plan.py
Generate improvement plan markdown files from database entries or prompts.

Usage:
```bash
python imple/V00_00_01/gen_improv_plan.py --plan-key my_plan
python imple/V00_00_01/gen_improv_plan.py --prompt "Create self-query interface"
```

## Project Structure

```
prj/self_learn/
├── 000_phase.md           # Entry point and overview
├── 001_phase.md           # Implementation requirements
├── README.md            # This file
├── docs/                # Project documentation
│   └── overview.md
├── rules/               # Governance rules
│   └── 001-rule-no_archive.md
├── imple/
│   └── V00_00_01/
│       ├── self_query.py            # Query interface
│       ├── gen_improv_plan.py       # Plan generation
│       └── test/
│           └── test_self_query.py   # Unit tests
└── plans/               # Work plans and executions
```

## Integration with Continuity.db

All self-improvement work is stored in continuity.db:
- `metacognitive_state` — Goals, focus, and aspect
- `work_plans` — Active work items
- `work_plan_steps` — Actionable steps with tracking
- `reasoning_episodes` — Audit trail of reasoning
- `journal` — Notes and reflections

## Running Tests

```bash
python -m pytest imple/V00_00_01/test/
```

Or directly:
```bash
python imple/V00_00_01/test/test_self_query.py
```

## Development

1. Set project goal:
   ```bash
   python project_command.py "project goal set self_learn Create self-improving infrastructure for cognition.db"
   ```

2. Query current state:
   ```bash
   python imple/V00_00_01/self_query.py status
   ```

3. Generate improvement plan:
   ```bash
   python imple/V00_00_01/gen_improv_plan.py --prompt "Improve the self-query interface for better recall"
   ```

## Vision

The self-learn project enables cognition.db to:
- Remember past reasoning and decisions
- Apply learned patterns to new problems
- Improve its own structure and policies
- Maintain coherent long-term reasoning
- Support safe, auditable self-modification