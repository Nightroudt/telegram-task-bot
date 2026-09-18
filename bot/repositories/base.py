from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


class BaseRepository(ABC, Generic[ModelT]):
    """Common CRUD primitives shared by all repositories.

    Subclasses set `model` to the SQLAlchemy entity they manage and inherit
    `get_by_id`/`delete` instead of re-implementing the same two queries in
    every repository. `model` is an abstract property so this base class
    cannot be instantiated on its own.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @property
    @abstractmethod
    def model(self) -> type[ModelT]: ...

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        """Unscoped lookup by primary key — no ownership check.

        Fine for entities with no owner (UserRepository, looking up a user by
        their own Telegram id). For anything with a per-user owner
        (TaskRepository), use a scoped method like get_owned() instead —
        get_by_id() would let one user's id guess reach another user's row.
        """
        return await self.db.get(self.model, entity_id)

    async def delete(self, entity: ModelT) -> None:
        await self.db.delete(entity)
        await self.db.commit()
