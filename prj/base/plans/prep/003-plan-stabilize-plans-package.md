---
id: 003-PLAN-STABILIZE-PLANS-PACKAGE
category: Plan Preparation
title: Stabilize the plans package with strict TDD execution
parent: ../
artifact_role: project-adapted
---

# Stabilize the plans package with strict TDD execution

## Scope

Repository under test:

`/home/peter/xmyrequi/myrequi/prj/continuity_db`

All new implementation work belongs under:

`prj/continuity_db/plans`

Execution log:

`tmp/plan-execution.log`

Provider error log:

`tmp/provider-error.log`

The runner SHALL create the workspace `tmp` directory when needed and append
step summaries, pytest commands/results, refactor notes, git commands, commit
IDs, and failures to the execution logfile. The logfile is runtime evidence
and SHALL not be committed.

If an LLM request returns an error, the runner SHALL append a timestamped
record containing the plan step, provider, request purpose, error, retry number,
and outcome to `tmp/provider-error.log`. It SHALL wait exactly two seconds,
retry the request once, and then issue the `continue` command automatically.
The retry and continue action SHALL also be recorded with timestamps. If the
retry still fails, `continue` SHALL resume the failure handler, which stops the
current step and preserves both logs for diagnosis; it SHALL not silently skip
the failed behavior.

Provider retry policy:

- LLM provider errors are transport/provider failures, not test failures.
- Retry exactly once after a two-second delay.
- After the retry attempt, issue `continue` automatically.
- Do not retry indefinitely or treat an error response as valid content.
- Record all provider-error, wait, retry, and continue events in
  `tmp/provider-error.log` using ISO-8601 timestamps.

Context budget constraint:

- Before starting each step, and during long-running execution, check the
  current context usage through the available context-information route.
- If context usage exceeds 50%, execute `/compact` before continuing.
- After compaction, re-read the active step state and continue from the last
  committed checkpoint.

Language: Python. Test framework: pytest. The work uses small, reversible
TDD cycles and requires a commit before progressing to the next step.

## Operating contract

Before each step, the plan runner SHALL automatically:

1. Append a concise **What happens next** summary to
   `tmp/plan-execution.log`.
2. Write failing tests first and append the exact pytest command/output.
3. Implement the smallest change that makes the tests pass.
4. Refactor only with the safety net green and append the refactor note.
5. Append and run `git add` and `git commit` with a clear imperative message.

No human approval is required. The runner SHALL execute the complete ordered
plan automatically, not stop after a convenient milestone. It SHALL stop only
on a test, refactor, or commit failure, append the failure details, and leave
the logfile for diagnosis. Otherwise it proceeds to the next step only after
the preceding step is green and committed.

## Comparable step evidence

Every step SHALL use the same log fields so results are directly comparable:

```text
timestamp | plan.step | phase | action | command | expected | actual | status
```

The runner SHALL record expected behavior before execution and actual pytest or
Git results afterward. A step is `GREEN` only when actual matches expected.

For every Git action, the logfile SHALL include:

- repository root and current branch;
- `git status --short` before staging;
- the exact `git add ...` command;
- the exact `git commit -m ...` command;
- commit exit status and resulting commit ID;
- `git status --short` after committing.

If a commit fails, the runner SHALL record the full failure and SHALL NOT
advance to the next step.

## Proposed nested plan sequence

### Plan 1: Establish the plans package boundary

- **Step 1.1: Inspect current plans structure**
  - Identify existing modules, tests, import paths, and package assumptions.
  - No code changes; emit the inspection result and continue automatically.
- **Step 1.2: Initialize package metadata**
  - Add only the minimal package files required by the existing project.
  - Add a focused importability test.
- **Step 1.3: Commit the package boundary**
  - Run the focused and relevant regression tests.
  - Commit the initialized package separately.

### Plan 2: Define the minimal plan interface

- **Step 2.1: Specify one plan result contract**
  - Add a failing test for the smallest stable plan interface.
- **Step 2.2: Implement the minimal interface**
  - Return a deterministic, typed result without adding execution policy.
- **Step 2.3: Refactor the interface**
  - Separate public types from implementation details.
  - Preserve the tested API and commit.

### Plan 3: Add sequential plan execution

- **Step 3.1: Test one plan executes once**
  - Arrange one plan, execute it, and assert its result and order.
- **Step 3.2: Test multiple plans execute in declaration order**
  - Assert no later plan starts before the prior plan completes.
- **Step 3.3: Test failure stops progression**
  - Assert the failing plan is reported and later plans are not run.
- **Step 3.4: Implement the minimal runner and refactor**
  - Keep execution deterministic and dependency-light.
  - Commit only after all runner tests pass.

### Plan 4: Add approval and test gates

- **Step 4.1: Require approval before a step begins**
  - Test that an unapproved step is paused or rejected.
- **Step 4.2: Require pytest success before commit progression**
  - Test the gate decision independently from shell execution.
- **Step 4.3: Require git commit before the next step**
  - Test the orchestration state transition without mutating a real repository.
- **Step 4.4: Implement and refactor the gates**
  - Keep subprocess and git operations behind injectable adapters.
  - Commit the gate behavior separately.

### Plan 5: Add plan discovery and reporting

- **Step 5.1: Discover numbered plan files**
  - Test deterministic ordering and ignored/non-plan files.
- **Step 5.2: Report RED, GREEN, REFACTOR, and commit evidence**
  - Test concise structured output for each lifecycle phase.
- **Step 5.3: Implement reporting and refactor**
  - Preserve machine-readable results and human-readable summaries.
  - Commit the reporting behavior.

### Plan 6: Add core/extension/SIT/UAT organization

- **Step 6.1: Define test-phase metadata**
  - Add pytest markers for `unit`, `sit`, and `uat`.
- **Step 6.2: Define component metadata**
  - Distinguish `core` and `extension.content_guard` without changing test behavior.
- **Step 6.3: Add phase-specific selection tests/configuration**
  - Verify focused commands select the intended tests.
- **Step 6.4: Apply only safe file moves after path assumptions are tested**
  - Commit test organization independently from implementation behavior.

### Plan 7: Full regression and documentation

- **Step 7.1: Run the complete pytest suite**
  - Record exact passing/skipped results.
- **Step 7.2: Document plan execution and rollback**
  - Add concise usage and recovery guidance.
- **Step 7.3: Final refactor and release commit**
  - Check PEP 8, type hints where useful, clean git state, and commit.

## Execution policy

The plan is an ordered execution queue, not a menu. After Step 1.1 completes,
the runner SHALL automatically continue through Step 1.2, Step 1.3, and all
later plans. It SHALL not require a new user request between logical steps.

The initial automatic execution step is **Plan 1, Step 1.1: Inspect current
plans structure**. The runner SHALL then continue through the complete nested
sequence while preserving the test, refactor, and Git gates above.
