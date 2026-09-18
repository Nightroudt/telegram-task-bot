from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.repositories.task_repo import TaskRepository
from bot.repositories.user_repo import UserRepository
from bot.services.task_service import TaskService
from bot.services.user_service import UserService


class DbSessionMiddleware(BaseMiddleware):
    """Opens one DB session per incoming update and injects ready-to-use
    services into handler kwargs — the aiogram equivalent of FastAPI's
    `Depends(get_db)`, since aiogram has no built-in DI for this.

    The session is closed after the handler returns, win or lose, so a
    failed handler can never leak a connection back to the pool.
    """

    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self._session_factory() as session:
            data["user_service"] = UserService(UserRepository(session))
            data["task_service"] = TaskService(TaskRepository(session))
            return await handler(event, data)
