# Plan 001: Robust Telegram send tests for special characters

## Goal
Ensure Telegram replies preserve or safely render special characters and formatting, while long replies are delivered completely across Telegram message boundaries.

## Scope
- Telegram polling response path in `prj/continuity_db/imple/V00.00.01/core/route/input_action_execution.py`.
- Telegram adapter send path where applicable.
- Mocked Telegram bot tests; no real bot messages or secrets.

## Test cases
1. Plain text containing `<`, `>`, `&`, quotes, apostrophes, underscores, brackets, and backslashes.
2. Markdown bold input such as `**bold**`, including adjacent punctuation.
3. Newlines, Unicode characters, emoji, and non-ASCII text.
4. A message exactly at the Telegram limit and one character beyond it.
5. A message containing special characters at a split boundary.
6. Routed responses with debug off: concise output with no technical leakage.
7. Routed responses with debug on: technical output remains available and is safely encoded.
8. Telegram API failure when HTML parsing rejects malformed content: verify a safe fallback or recorded failure, not silent truncation.

## Acceptance criteria
- Tests assert the exact text sent to the mocked bot, including all chunks and their order.
- HTML-sensitive characters are escaped; intended bold formatting renders correctly.
- No message chunk exceeds Telegram's limit (account for Telegram's UTF-16 length semantics).
- No characters disappear, duplicate, or become malformed at chunk boundaries.
- Debug-off responses contain no route names, handlers, JSON metadata, PIDs, paths, or stack traces unless explicitly intended as user-facing text.
- Tests run deterministically in the project `.venv` without network access.

## Implementation approach
1. Extract or retain a small pure formatter/chunker API so behavior can be tested without starting polling.
2. Use a fake Telegram bot recording `send_message` calls and `parse_mode`.
3. Add unit tests for formatter escaping and chunking.
4. Add an integration-style polling test with mocked receive input `X route status`.
5. Run focused tests, then the complete Telegram/route test subset.
6. Document the Telegram formatting and length assumptions.

## Commands
```bash
source .venv/bin/activate
PYTHONPATH=prj/continuity_db/imple/V00.00.01/core pytest -q \
  prj/continuity_db/imple/V00.00.01/test/unit/core/route
```

## Non-goals
- Sending test messages to the production Telegram bot.
- Changing route-recursion safety behavior.
- Exposing database contents or credentials.

## End condition
The focused and relevant regression tests pass, demonstrating lossless, safe Telegram delivery for special characters, formatting, and long responses.
