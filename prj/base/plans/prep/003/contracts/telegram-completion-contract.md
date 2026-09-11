# Telegram completion notification contract

On successful completion of a concrete plan, after the final repository/status
checks and before the terminal logfile archive, send one Telegram summary using
the project's configured Telegram route:

```text
telegram send <summary>
```

The summary MUST include:

- concrete plan ID and title;
- end condition and `END_CONDITION_MET` status;
- concise list of completed work;
- tests and their result;
- commit IDs and relevant references/paths;
- known limitations or follow-up items.

Use the configured default chat resolution; do not persist the token, chat ID,
or summary in the database. The notification is a completion side effect, not
a replacement for the execution log. If sending fails, record the failure and
report that the plan completed but notification delivery failed. Do not claim
notification delivery without a successful route result.

No completion notification is sent for a failed or incomplete plan.
