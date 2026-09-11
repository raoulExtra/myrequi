---
id: 003-PLAN-STABILIZE-PLANS-PACKAGE
category: Plan Preparation
title: Stabilize a plans package with strict TDD execution
parent: ../
artifact_role: reusable-plan-template
---

# Stabilize a plans package

This is a reusable meta-plan for Python projects and Python tasks. It defines
how to turn a requested task into a concrete, project-local implementation plan
and then execute that plan with strict TDD.

This file and `003/` are templates. They must not assume a repository, package
layout, database, test framework configuration, or end condition.

## Required initialization inputs

Before Step 1.1, collect and record:

- target project root;
- task statement and non-goals;
- Python version and test command;
- implementation and test roots;
- project-local plan directory;
- user-provided end condition;
- commit and remote-state requirements.

If any required input is missing, stop with a configuration error. Do not
execute implementation work.

## Concrete-plan creation

The first project-specific deliverable is a concrete plan created under the
related project, for example:

```text
<target-project>/plans/<plan-id>-<short-name>.md
<target-project>/plans/<plan-id>/01-...md
<target-project>/plans/<plan-id>/02-...md
```

The concrete plan must contain the target project's paths, commands, package
boundaries, test selectors, dependencies, acceptance criteria, rollback plan,
and the supplied end condition. It may select, reorder, or omit the generic
parts below after inspection. All implementation work and execution evidence
belong to the related project; this reusable template remains unchanged.

## Generic execution sequence

Use these parts only after adapting them into the concrete project plan:

1. `003/01-package-boundary.md`
2. `003/02-plan-interface.md`
3. `003/03-sequential-execution.md`
4. `003/04-approval-and-test-gates.md`
5. `003/05-discovery-and-reporting.md`
6. `003/06-test-organization.md`
7. `003/07-regression-and-documentation.md`

The concrete plan should include only the parts relevant to its Python task.

## Shared contracts

- `003/contracts/runner-contract.md`
- `003/contracts/logging-contract.md`
- `003/contracts/context-and-gates.md`

## Operating rule

This is an ordered execution queue, not a menu. The runner works from the
concrete project-local plan, commits each completed logical step in the target
repository, and stops on test, refactor, or commit failure. It terminates
only when the concrete plan records `END_CONDITION_MET`. After the final status
check, moving the active execution and provider-error logs to `done/` is the
final filesystem action; no action may follow the move.
