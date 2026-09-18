from html import escape

import structlog
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.services.user_service import UserService

logger = structlog.get_logger()


async def cmd_start(message: Message, user_service: UserService) -> None:
    if message.from_user is None:
        return

    user = await user_service.register(
        id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    logger.info("user_registered", user_id=user.id)

    await message.answer(
        f"Привет, {escape(user.full_name)}! Я помогу управлять задачами.\n\n"
        "Команды:\n"
        "/newtask <название> — создать задачу\n"
        "/tasks — список активных задач\n"
        "/done <id> — отметить выполненной\n"
        "/delete <id> — удалить задачу"
    )


def build_router() -> Router:
    """A fresh Router each call — aiogram routers can only be attached to
    one Dispatcher/parent at a time, so a module-level singleton would break
    the moment a second Dispatcher (e.g. in tests) tries to include it."""
    router = Router(name="start")
    router.message.register(cmd_start, CommandStart())
    return router
