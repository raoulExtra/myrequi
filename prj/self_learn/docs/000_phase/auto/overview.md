# Phase 0 Documentation

## Overview
Phase 0 establishes the foundational self-improving infrastructure for the self_learn project workspace.

## Key Components

### Purpose
Establish the foundational self-improving infrastructure for the self_learn project workspace.

### Goal
Enable the cognition.db system to support precise working in phased projects through automation that keeps the AI focused on high-impact tasks.

### Core Requirements

#### CR0: Subprojects Structure
- **auto** - Directory for automatic project handling tools and configurations
- **auto/sim** - Directory for simulation-specific infrastructure and test scenarios
- Subproject structure must support independent versioning and documentation
- Each subproject inherits core requirements but may extend them

#### CR1: Meta-Learning Improvement
- The system must record its improvement actions and outcomes to continuity.db
- Each self-improvement cycle must produce an audit trail
- The system must identify at least 3 improvement patterns from past cycles
- Quality metrics (before/after) must be measurable per improvement

#### CR2: Filesystem State Management
- metacognitive_state.json must be tracked by git version control
- State changes must include ISO 8601 timestamps
- At least 5 state keys must be migratable
- State must be readable via `self_query.py status`

#### CR3: Automated Plan Generation
- Plans must be generable from JSON state entries using gen_improv_plan.py
- Generated plans must include executable steps with clear success criteria
- At least 3 plan types must be auto-generating
- Plans must inherit structure from plan templates

#### CR4: Embedded Learning Loop
- Observe: Query memory for relevant context via self_query.py
- Update: Apply changes through pi command or pi_query.py
- Verify: Compare before/after states with measurable metrics
- Reuse: Store patterns in reasoning_episodes table or JSON files

#### CR5: Learning Domain Separation
- Project-specific learnings must be stored in `prj/self_learn/knowledge/`
- General continuity.db learnings remain in the main database
- Each storage location must have a clear ownership marker
- Cross-referencing between domains must use unique trace IDs

## Navigation
- [Phase 1](../001_phase.md) - Core implementation of self-improvement tools
- [Rules](../rules/) - Governance rules for self-improvement
- [Implementation](../imple/) - Versioned implementations

## Structure
Recommended subdirectories following project conventions:
- `docs/` — overview, usage, project explanation
- `examples/` — sample outputs or mock content
- `references/` — copied links to standards/specs
- `assets/` — images, diagrams, screenshots
- `archive/` — old or superseded material
- `decisions/` — project relevant decisions
- `imple/<version>/` — implementation snapshots
- `plans/` — work_plan templates and executions
- `auto/` — automatic project handling tools
- `auto/sim/` — simulation infrastructure

## Tags
- thinking_workspace
- self_improvement

## Status
active

## Versions
- V00_00_01 — Initial phase structure and pi_query implementation

## Default version
V00_00_01