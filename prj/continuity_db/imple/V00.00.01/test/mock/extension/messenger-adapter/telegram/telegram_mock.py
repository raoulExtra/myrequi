"""Deterministic python-telegram-bot stand-ins for extension tests.

This mock does not import python-telegram-bot, contact Telegram, or require a
bot token. It models the small async surface normally used by a messenger
adapter: updates, messages, contexts, and outgoing bot messages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


@dataclass(frozen=True)
class MockUser:
    id: int = 1001
    username: str = "mock-user"
    is_bot: bool = False


@dataclass(frozen=True)
class MockChat:
    id: int = 2001
    type: str = "private"


@dataclass
class MockMessage:
    text: str = ""
    chat: MockChat = field(default_factory=MockChat)
    from_user: MockUser = field(default_factory=MockUser)
    replies: list[str] = field(default_factory=list)

    async def reply_text(self, text: str, **kwargs: Any) -> "MockMessage":
        """Record a reply using the same async shape as PTB Message."""
        del kwargs
        self.replies.append(text)
        return self


@dataclass
class MockUpdate:
    message: MockMessage | None = None
    update_id: int = 1

    @property
    def effective_message(self) -> MockMessage | None:
        return self.message

    @property
    def effective_chat(self) -> MockChat | None:
        return self.message.chat if self.message else None

    @property
    def effective_user(self) -> MockUser | None:
        return self.message.from_user if self.message else None

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        chat_id: int = 2001,
        user_id: int = 1001,
        username: str = "mock-user",
        update_id: int = 1,
    ) -> "MockUpdate":
        return cls(
            message=MockMessage(
                text=text,
                chat=MockChat(id=chat_id),
                from_user=MockUser(id=user_id, username=username),
            ),
            update_id=update_id,
        )


@dataclass
class SentMessage:
    chat_id: int
    text: str
    kwargs: dict[str, Any]


@dataclass
class MockBot:
    """Bot double that records outbound messages instead of using the network."""

    token: str | None = field(default=None, repr=False)
    sent_messages: list[SentMessage] = field(default_factory=list)

    async def send_message(self, chat_id: int, text: str, **kwargs: Any) -> SentMessage:
        sent = SentMessage(chat_id=chat_id, text=text, kwargs=kwargs)
        self.sent_messages.append(sent)
        return sent


@dataclass
class MockContext:
    bot: MockBot = field(default_factory=MockBot)
    args: list[str] = field(default_factory=list)
    user_data: dict[str, Any] = field(default_factory=dict)
    chat_data: dict[str, Any] = field(default_factory=dict)


Handler = Callable[[MockUpdate, MockContext], Awaitable[Any]]


@dataclass
class MockApplication:
    """Minimal application double for dispatching one handler in tests."""

    handler: Handler | None = None
    bot: MockBot = field(default_factory=MockBot)

    def add_handler(self, handler: Handler) -> None:
        self.handler = handler

    async def process_update(
        self, update: MockUpdate, *, args: list[str] | None = None
    ) -> Any:
        if self.handler is None:
            raise RuntimeError("No mock Telegram handler configured")
        context = MockContext(bot=self.bot, args=args or [])
        return await self.handler(update, context)


def make_text_update(text: str, **kwargs: Any) -> MockUpdate:
    """Convenience factory for adapter tests."""
    return MockUpdate.from_text(text, **kwargs)
