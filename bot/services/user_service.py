from bot.repositories.user_repo import UserRepository
from bot.schemas.user import UserRead


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def register(self, *, id: int, username: str | None, full_name: str) -> UserRead:
        """Register a user on /start, or return their existing record.

        Idempotent: /start can be sent any number of times (Telegram will
        also redeliver it after certain client reconnects) without ever
        raising a duplicate-primary-key error.
        """
        existing = await self._user_repo.get_by_id(id)
        if existing is not None:
            return UserRead.model_validate(existing)

        created = await self._user_repo.create(id=id, username=username, full_name=full_name)
        return UserRead.model_validate(created)
