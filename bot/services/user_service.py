from bot.repositories.user_repo import UserRepository
from bot.schemas.user import UserRead


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def register(self, *, id: int, username: str | None, full_name: str) -> UserRead:
        """Register a user on /start, or return their existing record.

        Idempotent: /start can be sent any number of times (Telegram will
        also redeliver it after certain client reconnects, or two updates
        can arrive back to back) without ever raising a duplicate-primary-key
        error — see UserRepository.get_or_create for how the race is closed.
        """
        user = await self._user_repo.get_or_create(id=id, username=username, full_name=full_name)
        return UserRead.model_validate(user)
