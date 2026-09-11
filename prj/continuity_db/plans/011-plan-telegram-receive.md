---
id: 011-PLAN-TELEGRAM-RECEIVE
category: Concrete Project Plan
project: prj/continuity_db
parent: ../../base/plans/prep/003-plan-stabilize-plans-package.md
status: active
---

# Add one-update Telegram receive route

## End condition

The Telegram adapter asynchronously retrieves one pending update through
python-telegram-bot `Bot.get_updates`, extracts its chat ID and message text,
and exposes it through `telegram receive`. No token or message is persisted.
Mock-focused and full regression tests pass before `END_CONDITION_MET`.
