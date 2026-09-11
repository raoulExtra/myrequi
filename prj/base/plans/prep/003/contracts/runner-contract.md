# Runner contract

Before each concrete-plan step, record a concise **What happens next** entry,
write failing tests first, run the exact project test command, implement the
smallest passing change, refactor only while green, and commit before advancing.

The concrete plan is an ordered queue, not a menu. Stop on test, refactor, or
commit failure. Each step uses:

```text
timestamp | plan.step | phase | action | command | expected | actual | status
```

For Git actions record the target repository, branch, pre-stage status, exact
`git add`, exact `git commit -m`, exit status, commit ID, and post-commit status.
Use the concrete plan ID in commit subjects, for example `<PLAN-ID>: ...`.
