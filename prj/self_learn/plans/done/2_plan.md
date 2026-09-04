# Self-learn next-step automation plan

status: completed

## objective
Make the self_learn filesystem update itself more automatically by generating indexes and keeping the workspace current.

## steps
1. Add a docs index that is generated from the current filesystem.
2. Add a refresh action that syncs the tree and rewrites the index.
3. Keep the plan/output flow simple so the project can repeat it.
4. Verify the automation with tests.
5. Add a checkpoint command that stages the project and records a git commit at the phase boundary.
