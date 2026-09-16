from bot.models.user import User
from bot.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def create(self, *, id: int, username: str | None, full_name: str) -> User:
        user = User(id=id, username=username, full_name=full_name)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
