# Requirement: Plan generation from memory

## Overview
Generate numbered markdown plan files from continuity.db work_plans, enabling systematic improvement tracking.

## Rationale
The system should be able to:
1. Generate plan documents from DB entries
2. Export linked plans recursively
3. Track plan execution status
4. Support both DB plans and prompt-based plans

## Detailed specification
- Module: `gen_improv_plan.py` (similar to plans/gen_plan.py)
- Input: plan_key(s) or prompt text
- Output: numbered markdown file (e.g., `1_plan.md`)
- Features:
  - Extract title, objective, prompt from work_plans table
  - Include linked plans recursively
  - Generate numbered step lists from prompt guidance
  - Follow existing plan markdown format

## Success criteria
- Can generate plan from a known plan_key
- Can generate plan from prompt text
- Output follows the project's plan format