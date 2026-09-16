import math

from bot.repositories.task_repo import TaskRepository
from bot.schemas.task import TaskPage, TaskRead
from bot.services.errors import TaskNotFoundError

PAGE_SIZE = 5


class TaskService:
    def __init__(self, task_repo: TaskRepository) -> None:
        self._task_repo = task_repo

    async def create_task(self, *, user_id: int, title: str) -> TaskRead:
        task = await self._task_repo.create(user_id=user_id, title=title)
        return TaskRead.model_validate(task)

    async def list_page(self, *, user_id: int, page: int) -> TaskPage:
        """List a user's active (not-done) tasks, 1-indexed page number."""
        page = max(page, 1)
        offset = (page - 1) * PAGE_SIZE

        tasks, total = await self._task_repo.list_active_page(
            user_id=user_id, limit=PAGE_SIZE, offset=offset
        )
        total_pages = max(math.ceil(total / PAGE_SIZE), 1)

        return TaskPage(
            items=[TaskRead.model_validate(t) for t in tasks],
            page=page,
            total_pages=total_pages,
            total=total,
        )

    async def complete_task(self, *, user_id: int, task_id: int) -> TaskRead:
        task = await self._task_repo.get_owned(task_id=task_id, user_id=user_id)
        if task is None:
            raise TaskNotFoundError
        completed = await self._task_repo.mark_done(task)
        return TaskRead.model_validate(completed)

    async def delete_task(self, *, user_id: int, task_id: int) -> None:
        task = await self._task_repo.get_owned(task_id=task_id, user_id=user_id)
        if task is None:
            raise TaskNotFoundError
        await self._task_repo.delete(task)
