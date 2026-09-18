from sqlalchemy.exc import IntegrityError

from bot.models.user import User
from bot.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def create(self, *, id: int, username: str | None, full_name: str) -> User:
        user = User(id=id, username=username, full_name=full_name)
        self.db.add(user)
        # No db.refresh(): Postgres/asyncpg's implicit RETURNING support
        # already populates created_at on commit — a refresh would just be a
        # second, redundant round trip.
        await self.db.commit()
        return user

    async def get_or_create(self, *, id: int, username: str | None, full_name: str) -> User:
        """Idempotent /start registration, safe under concurrent calls.

        A plain "check then create" has a race: two updates for the same
        user (e.g. Telegram redelivering /start, or a fast double-tap)
        opened via separate sessions can both see "not found" before either
        commits, and the second INSERT then violates the users.id primary
        key. Catching that and re-fetching closes the window instead of
        letting an IntegrityError escape as an unhandled crash.
        """
        existing = await self.get_by_id(id)
        if existing is not None:
            return existing

        try:
            return await self.create(id=id, username=username, full_name=full_name)
        except IntegrityError:
            await self.db.rollback()
            existing = await self.get_by_id(id)
            if existing is None:
                raise
            return existing
