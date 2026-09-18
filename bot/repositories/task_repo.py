from datetime import UTC, datetime

from sqlalchemy import func, select

from bot.models.task import Task
from bot.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    model = Task

    async def create(self, *, user_id: int, title: str) -> Task:
        task = Task(user_id=user_id, title=title)
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_owned(self, *, task_id: int, user_id: int) -> Task | None:
        """Fetch a task only if it belongs to user_id.

        Used by /done and /delete so one user can never act on another
        user's task id, even if they guess it.
        """
        result = await self.db.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def count_active(self, *, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.user_id == user_id, Task.is_done.is_(False))
        )
        return result.scalar_one()

    async def list_active(self, *, user_id: int, limit: int, offset: int) -> list[Task]:
        result = await self.db.execute(
            select(Task)
            .where(Task.user_id == user_id, Task.is_done.is_(False))
            .order_by(Task.created_at, Task.id)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def mark_done(self, task: Task) -> Task:
        task.is_done = True
        task.completed_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(task)
        return task
