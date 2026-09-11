---
id: 009-PLAN-TELEGRAM-DEFAULT-CHAT
category: Concrete Project Plan
project: prj/continuity_db
parent: ../../base/plans/prep/003-plan-stabilize-plans-package.md
status: active
---

# Resolve Telegram default chat from getUpdates

## End condition

The Telegram send route accepts both an explicit chat ID and a default-chat form.
When no chat ID is supplied, the adapter uses python-telegram-bot
`Bot.get_updates()` and selects the latest `effective_chat.id`. No chat ID or
bot token is persisted. Focused and full regression tests pass before
`END_CONDITION_MET`.
