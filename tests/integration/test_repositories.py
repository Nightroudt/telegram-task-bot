from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.repositories.task_repo import TaskRepository
from bot.repositories.user_repo import UserRepository


async def test_user_repository_create_and_get_by_id(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)

    created = await repo.create(id=1, username="eleu", full_name="Eleu K")
    fetched = await repo.get_by_id(1)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.username == "eleu"


async def test_get_or_create_recovers_from_a_concurrent_registration_race(
    session_factory: async_sessionmaker,
) -> None:
    """Simulates two /start updates for the same user racing each other:
    DbSessionMiddleware gives each its own session, so both can see "not
    found" before either commits. Whichever loses the INSERT must recover
    instead of letting IntegrityError crash that update."""
    async with session_factory() as session_a, session_factory() as session_b:
        repo_a = UserRepository(session_a)
        repo_b = UserRepository(session_b)

        assert await repo_a.get_by_id(777) is None
        assert await repo_b.get_by_id(777) is None

        winner = await repo_a.create(id=777, username="a", full_name="Winner")
        assert winner.id == 777

        loser_result = await repo_b.get_or_create(id=777, username="b", full_name="Loser")

        assert loser_result.id == 777
        assert loser_result.full_name == "Winner"


async def test_task_repository_create_and_list_active(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    tasks = TaskRepository(db_session)
    await users.create(id=1, username=None, full_name="Eleu K")

    await tasks.create(user_id=1, title="Buy milk")
    await tasks.create(user_id=1, title="Write tests")

    total = await tasks.count_active(user_id=1)
    items = await tasks.list_active(user_id=1, limit=10, offset=0)

    assert total == 2
    assert [t.title for t in items] == ["Buy milk", "Write tests"]


async def test_completed_tasks_are_excluded_from_active_list(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    tasks = TaskRepository(db_session)
    await users.create(id=1, username=None, full_name="Eleu K")
    task = await tasks.create(user_id=1, title="Buy milk")

    await tasks.mark_done(task)

    assert await tasks.count_active(user_id=1) == 0
    assert await tasks.list_active(user_id=1, limit=10, offset=0) == []


async def test_get_owned_returns_none_for_a_different_users_task(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    tasks = TaskRepository(db_session)
    await users.create(id=1, username=None, full_name="Owner")
    await users.create(id=2, username=None, full_name="Intruder")
    task = await tasks.create(user_id=1, title="Private task")

    assert await tasks.get_owned(task_id=task.id, user_id=2) is None
    assert await tasks.get_owned(task_id=task.id, user_id=1) is not None


async def test_task_list_is_isolated_per_user(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    tasks = TaskRepository(db_session)
    await users.create(id=1, username=None, full_name="A")
    await users.create(id=2, username=None, full_name="B")
    await tasks.create(user_id=1, title="A's task")
    await tasks.create(user_id=2, title="B's task")

    assert [t.title for t in await tasks.list_active(user_id=1, limit=10, offset=0)] == ["A's task"]
    assert [t.title for t in await tasks.list_active(user_id=2, limit=10, offset=0)] == ["B's task"]
