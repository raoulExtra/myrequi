# Working rules

These rules keep automation changes and verification aligned.

## rules

- Change automation and the related tests in the same commit.
- If behavior is changing, write the expected behavior in tests first or alongside the code.
- If an active plan exists, generate a handoff and store its execution record under plans/done/.
- Keep generated docs and source docs in sync.
- Prefer a small rule that can be checked over a vague rule that can be forgotten.

## use

This file captures the working rule we just agreed on for the project.
It is a short companion doc so the rule is visible in the filesystem.
