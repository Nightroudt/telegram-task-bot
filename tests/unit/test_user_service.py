from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from bot.models.user import User
from bot.services.user_service import UserService


def make_user(id: int, username: str | None = "eleu", full_name: str = "Eleu K") -> User:
    return User(id=id, username=username, full_name=full_name, created_at=datetime.now(UTC))


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(repo: AsyncMock) -> UserService:
    return UserService(repo)


async def test_register_creates_new_user_when_none_exists(
    service: UserService, repo: AsyncMock
) -> None:
    repo.get_by_id.return_value = None
    repo.create.return_value = make_user(id=777)

    result = await service.register(id=777, username="eleu", full_name="Eleu K")

    repo.create.assert_awaited_once_with(id=777, username="eleu", full_name="Eleu K")
    assert result.id == 777


async def test_register_is_idempotent_for_existing_user(
    service: UserService, repo: AsyncMock
) -> None:
    repo.get_by_id.return_value = make_user(id=777)

    result = await service.register(id=777, username="eleu", full_name="Eleu K")

    repo.create.assert_not_awaited()
    assert result.id == 777
