---
id: 002-PLAN-REFACTOR-MODULARISATION
category: Plan Preparation
title: Stable Modularisation Refactoring Prompt
parent: ../
artifact_role: project-adapted
---

# Stable Modularisation Refactoring Prompt

You are a senior software architect specializing in stable, modular system design (SOLID, clean boundaries, minimal coupling).

## Context

- **Language/Framework:** [e.g. Python 3.12, FastAPI]
- **Project purpose:** [1–2 sentences]
- **Key directories/files:** [list or attach]
- **Existing tests:** [yes/no; brief note]
- **Constraints:** [e.g. no new dependencies, must stay backward compatible, must run on X]

## Current code

```<language>
# paste the relevant module(s) or a summary of the structure
```

## Goal

Propose and then apply a **stable modularisation** of this codebase so that:

1. Each module has a single, clear responsibility and a small, stable public API.
2. Internal details are hidden; other modules depend only on public interfaces.
3. Dependencies form a clear, acyclic graph with no circular imports.
4. The design supports likely future changes with minimal ripple effects.

## Design principles

Apply these principles explicitly:

- **SOLID**, especially SRP, ISP, and DIP.
- **DRY:** extract shared logic, but avoid premature abstraction.
- Prefer composition over inheritance where it reduces coupling.
- Keep modules reasonably sized, aiming for fewer than 500 lines per module where possible.

## Process

### 1. Understand & Summarize

- Briefly explain what the current code does.
- Identify the main god objects, long functions, and tightly coupled areas.

### 2. Propose Module Structure

For each proposed module, provide:

- Name and single responsibility in one sentence.
- Responsibilities, with 3–5 bullets.
- Non-responsibilities: 2–3 things it does **not** handle.
- Public interface: exported functions/classes and signatures/types.
- Dependencies on other modules and why.
- Estimated size in files/lines.

Also describe:

- Allowed and forbidden dependencies between modules. For example: `domain → infra` may be allowed, while `infra → domain` may be forbidden.
- Where shared types/constants live and what must never be shared.

### 3. Future-Change Test

Given these likely changes: [list 2–4], show which single module would absorb each change and why the other modules remain stable.

### 4. Refactoring Plan: Stable & Incremental

Break the work into the smallest safe steps so that:

- After each step the code still runs and tests pass.
- Each step is a single, reviewable commit.
- Earlier steps do not depend on later ones.

For each step, specify:

- What changes: files/functions.
- How to verify it: tests, behaviors, or assertions.
- Rollback plan if something breaks.
- Risk: `LOW`, `MEDIUM`, or `HIGH`, with justification.

### 5. Apply Step 1 Only

- Implement only the first refactoring step.
- Show before/after code for the changed files.
- Explain why this step is safe and how it improves modularity.

## Required output format

Use exactly these sections:

- `Summary`
- `Current Smells`
- `Proposed Modules`
- `Future-Change Test`
- `Refactoring Plan`
- `Step 1: <name>`

Use fenced code blocks for code. Keep explanations concise and concrete.
