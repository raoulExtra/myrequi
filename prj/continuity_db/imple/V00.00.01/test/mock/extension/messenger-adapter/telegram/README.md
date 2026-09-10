# Mock Telegram messenger

Deterministic test doubles for a future `python-telegram-bot` messenger
adapter.

This directory deliberately does not import `python-telegram-bot`, use a bot
token, or contact Telegram. `telegram_mock.py` provides updates, messages,
contexts, an outbound-message recorder, and a minimal async application
surface for unit tests.
