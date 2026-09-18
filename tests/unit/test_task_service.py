from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from bot.models.task import Task
from bot.services.errors import TaskNotFoundError
from bot.services.task_service import PAGE_SIZE, TaskService


def make_task(id: int, user_id: int = 1, title: str = "t", is_done: bool = False) -> Task:
    return Task(
        id=id,
        user_id=user_id,
        title=title,
        is_done=is_done,
        created_at=datetime.now(UTC),
        completed_at=None,
    )


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(repo: AsyncMock) -> TaskService:
    return TaskService(repo)


async def test_create_task_delegates_to_repository_and_returns_read_model(
    service: TaskService, repo: AsyncMock
) -> None:
    repo.create.return_value = make_task(id=1, user_id=5, title="Buy milk")

    result = await service.create_task(user_id=5, title="Buy milk")

    repo.create.assert_awaited_once_with(user_id=5, title="Buy milk")
    assert result.id == 1
    assert result.title == "Buy milk"


async def test_list_page_computes_offset_and_total_pages(
    service: TaskService, repo: AsyncMock
) -> None:
    repo.count_active.return_value = 12
    repo.list_active.return_value = [make_task(id=6), make_task(id=7)]

    page = await service.list_page(user_id=1, page=2)

    repo.list_active.assert_awaited_once_with(user_id=1, limit=PAGE_SIZE, offset=PAGE_SIZE)
    assert page.page == 2
    assert page.total == 12
    assert page.total_pages == 3
    assert [t.id for t in page.items] == [6, 7]


async def test_list_page_clamps_page_below_one(service: TaskService, repo: AsyncMock) -> None:
    repo.count_active.return_value = 3
    repo.list_active.return_value = [make_task(id=1)]

    page = await service.list_page(user_id=1, page=-5)

    assert page.page == 1
    repo.list_active.assert_awaited_once_with(user_id=1, limit=PAGE_SIZE, offset=0)


async def test_list_page_clamps_page_above_total_pages(
    service: TaskService, repo: AsyncMock
) -> None:
    """A page number can go stale (e.g. deleting the last task on page 2
    shrinks total_pages) — list_page must fall back to the last valid page
    instead of returning an out-of-range, empty result."""
    repo.count_active.return_value = 3  # -> 1 page at PAGE_SIZE=5
    repo.list_active.return_value = [make_task(id=1)]

    page = await service.list_page(user_id=1, page=99)

    assert page.page == 1
    assert page.total_pages == 1
    repo.list_active.assert_awaited_once_with(user_id=1, limit=PAGE_SIZE, offset=0)


async def test_list_page_with_zero_tasks_reports_a_single_empty_page(
    service: TaskService, repo: AsyncMock
) -> None:
    repo.count_active.return_value = 0
    repo.list_active.return_value = []

    page = await service.list_page(user_id=1, page=1)

    assert page.total_pages == 1
    assert page.items == []


async def test_complete_task_raises_when_not_owned(service: TaskService, repo: AsyncMock) -> None:
    repo.get_owned.return_value = None

    with pytest.raises(TaskNotFoundError):
        await service.complete_task(user_id=1, task_id=999)

    repo.mark_done.assert_not_awaited()


async def test_complete_task_marks_owned_task_done(service: TaskService, repo: AsyncMock) -> None:
    task = make_task(id=1, user_id=5)
    repo.get_owned.return_value = task
    repo.mark_done.return_value = make_task(id=1, user_id=5, is_done=True)

    result = await service.complete_task(user_id=5, task_id=1)

    repo.get_owned.assert_awaited_once_with(task_id=1, user_id=5)
    repo.mark_done.assert_awaited_once_with(task)
    assert result.is_done is True


async def test_delete_task_raises_when_not_owned(service: TaskService, repo: AsyncMock) -> None:
    repo.get_owned.return_value = None

    with pytest.raises(TaskNotFoundError):
        await service.delete_task(user_id=1, task_id=999)

    repo.delete.assert_not_awaited()


async def test_delete_task_deletes_owned_task(service: TaskService, repo: AsyncMock) -> None:
    task = make_task(id=1, user_id=5)
    repo.get_owned.return_value = task

    await service.delete_task(user_id=5, task_id=1)

    repo.delete.assert_awaited_once_with(task)
