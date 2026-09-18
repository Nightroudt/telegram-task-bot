"""A minimal stand-in for aiogram's (nonexistent) official test client.

aiogram ships no TestClient like FastAPI's. The documented pattern instead
is to subclass BaseSession and override make_request() so it never hits the
real Bot API — Bot(session=FakeTelegramSession()) plus
Dispatcher.feed_update() then drives the real handler/middleware/keyboard
code exactly as production would, just without a network call at the edge.
"""

import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.methods import TelegramMethod
from aiogram.methods.answer_callback_query import AnswerCallbackQuery
from aiogram.methods.edit_message_text import EditMessageText
from aiogram.methods.send_message import SendMessage
from aiogram.types import CallbackQuery, Chat, Update
from aiogram.types import Message as TgMessage
from aiogram.types import User as TgUser


class FakeTelegramSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.sent: list[TelegramMethod] = []

    async def close(self) -> None:
        pass

    async def make_request(self, bot: Bot, method: TelegramMethod, timeout: int | None = None):
        self.sent.append(method)
        if isinstance(method, SendMessage | EditMessageText):
            return TgMessage(
                message_id=len(self.sent),
                date=datetime.datetime.now(datetime.UTC),
                chat=Chat(id=method.chat_id, type="private"),
                text=method.text,
            )
        if isinstance(method, AnswerCallbackQuery):
            return True
        return True

    async def stream_content(self, *args, **kwargs):
        yield b""


def make_message_update(user_id: int, text: str, update_id: int) -> Update:
    chat = Chat(id=user_id, type="private")
    user = TgUser(id=user_id, is_bot=False, first_name="Eleu")
    message = TgMessage(
        message_id=update_id,
        date=datetime.datetime.now(datetime.UTC),
        chat=chat,
        from_user=user,
        text=text,
    )
    return Update(update_id=update_id, message=message)


def make_callback_update(user_id: int, data: str, update_id: int) -> Update:
    chat = Chat(id=user_id, type="private")
    user = TgUser(id=user_id, is_bot=False, first_name="Eleu")
    orig_message = TgMessage(
        message_id=1,
        date=datetime.datetime.now(datetime.UTC),
        chat=chat,
        from_user=user,
        text="placeholder",
    )
    query = CallbackQuery(
        id=str(update_id), from_user=user, chat_instance="fake", message=orig_message, data=data
    )
    return Update(update_id=update_id, callback_query=query)


class FakeClient:
    """Thin wrapper so tests can read like a conversation: client.send(...),
    client.click(...)."""

    def __init__(self, bot: Bot, dp: Dispatcher, session: FakeTelegramSession) -> None:
        self.bot = bot
        self.dp = dp
        self.session = session
        self._update_id = 0

    async def send(self, user_id: int, text: str) -> TelegramMethod:
        self._update_id += 1
        await self.dp.feed_update(self.bot, make_message_update(user_id, text, self._update_id))
        return self.session.sent[-1]

    async def click(self, user_id: int, callback_data: str) -> TelegramMethod:
        self._update_id += 1
        await self.dp.feed_update(
            self.bot, make_callback_update(user_id, callback_data, self._update_id)
        )
        return self.session.sent[-1]
