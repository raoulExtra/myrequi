---
id: 008-PLAN-TELEGRAM-SEND-ROUTE
category: Concrete Project Plan
project: prj/continuity_db
parent: ../../base/plans/prep/003-plan-stabilize-plans-package.md
status: active
---

# Pin Telegram dependency and add send route

## End condition

The Telegram code artifact declares `python-telegram-bot==22.8`, the real
Telegram adapter calls the python-telegram-bot `Bot.send_message` API, and an
enabled routed action accepts `telegram send <chat_id> <message>`. Tokens remain
hidden, environment-first, and unpersisted. Mock tests and the full regression
suite pass before `END_CONDITION_MET`.
