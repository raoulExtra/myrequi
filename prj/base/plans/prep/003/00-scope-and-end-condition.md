# Plan 0: Intake and concrete-plan creation

This part is executed separately for each target project and Python task.

## Required intake

Record:

- target project root and repository;
- task statement and explicit non-goals;
- Python version, dependencies, and test command;
- implementation, test, and artifact roots;
- project-local plan directory;
- user-provided end condition;
- commit, branch, and remote-state requirements.

Inspect the target project before selecting implementation parts. Do not assume
that it uses the same package layout, test markers, database, or tooling as
another project.

## Concrete plan output

Create a plan in the related project, not only in this reusable template:

```text
<target-project>/plans/<plan-id>-<short-name>.md
<target-project>/plans/<plan-id>/01-<deliverable>.md
<target-project>/plans/<plan-id>/02-<deliverable>.md
```

The concrete plan must map each selected generic part to actual files, symbols,
commands, tests, acceptance evidence, rollback steps, and commits. It must
state which parts are intentionally omitted.

## End condition

Require a non-empty end condition from the user and copy it verbatim into the
concrete project-local plan. Do not substitute a generic example or invent one.

The runner evaluates the end condition against repository evidence: runtime
behavior, tests, commits, and required remote state. The plan may terminate
only after recording `END_CONDITION_MET`, its evidence, and timestamp in the
active execution log.

The terminal sequence is strict:

1. Record `END_CONDITION_MET` and evidence in the active execution log.
2. Run and record the final required repository/status checks.
3. Record the names and archive operation for both active logfiles.
4. Move the active execution and provider-error logfiles to the target
   project's `done/` directory.
5. Perform no further filesystem, Git, or log actions. The logfile move is the
   final action. Report `END of PLAN reached` only after the move completes.
