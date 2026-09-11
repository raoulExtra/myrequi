# Logging contract

The concrete project plan must choose its execution-log and provider-error-log
paths. At initialization, create the target project's log directory and archive
any pre-existing active logs into a local `done/` directory with UTC timestamps,
preserving contents and avoiding overwrite. Record that initialization archive
before continuing.

Require and record a non-empty user-provided end condition before the first
implementation step. Append step summaries, pytest results, refactor notes,
Git commands, commit IDs, and failures. Runtime logs must not be committed
unless the concrete project explicitly requires that as an artifact.

On successful completion, record the Telegram completion-summary attempt and
its route result before logfile archival. The summary must reference the plan,
end condition, completed work, tests, commits, paths, and limitations. Do not
persist the token, chat ID, or summary in the database.

On provider errors, record timestamp, step, provider, purpose, error, retry,
and outcome; wait exactly two seconds, retry once, issue `continue`, and stop on
a second failure.

## Terminal log protocol

The plan cannot finish without an exact `END_CONDITION_MET` record. After that
record and the final repository/status checks, write the planned archive names
to the active execution log, then move both active logfiles to `done/` with UTC
timestamps and no overwrite. The move is the final filesystem action: do not
append, commit, or modify anything afterward. Report `END of PLAN reached` only
when both moves succeed. The Telegram completion notification must therefore
be sent and its outcome recorded before either move; a failed notification is
reported as a delivery failure, not as a plan failure if the end condition was
already met.
