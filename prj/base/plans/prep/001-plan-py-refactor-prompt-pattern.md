---
id: 001-PLAN-PY-REFACTOR-PROMPT-PATTERN
category: Plan Preparation
title: Python Refactoring Prompt Pattern
parent: ../
artifact_role: project-adapted
---

# Python Refactoring Review Prompt

You are a senior Python engineer specializing in refactoring for readability, maintainability, and SOLID principles.

## Context

- **Language/Framework:** Python 3.12, FastAPI
- **Module purpose:** [1–2 sentences]
- **Key files:** [list or paste relevant files]
- **Existing tests:** [yes/no; if yes, brief note]

## Current code

```python
# paste the function/module/class here
```

## Goals

In priority order:

1. Improve readability and reduce complexity without changing behavior.
2. Extract long functions and reduce nesting.
3. Apply PEP 8 and project style: snake_case, type hints, and docstrings.
4. Keep the public API—function names, signatures, and return types—unchanged.

## Constraints

- Do not change behavior or external interfaces.
- Do not remove or rewrite existing comments/docstrings unless they are clearly wrong. If you change them, show the diff.
- Assume no new dependencies can be added.
- If something is unclear, ask up to three clarifying questions before refactoring.

## Process

1. Briefly explain what the code does in plain English.
2. List the top 3–5 code smells, with line references.
3. Propose a step-by-step refactoring plan, starting with the lowest-risk change.
4. Apply **only the first step** of that plan and show:
   - the before/after code for that step;
   - a short explanation of why it is safe and what changed.

## Required output format

Use exactly these sections:

- `Understanding`
- `Code Smells`
- `Refactoring Plan`
- `Step 1: <name>`

Use fenced code blocks for code.
