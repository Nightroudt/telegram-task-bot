import pytest_asyncio
from aiogram import Bot, Dispatcher
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from bot.handlers import build_router
from bot.middlewares import DbSessionMiddleware
from bot.models import Base
from tests.integration.fake_telegram import FakeClient, FakeTelegramSession


@pytest_asyncio.fixture
async def engine() -> AsyncEngine:
    # StaticPool pins every checkout to the *same* underlying connection, so
    # this in-memory SQLite database survives across the multiple separate
    # sessions DbSessionMiddleware opens per update. Without it, the default
    # pool can silently hand out a fresh (and empty) ":memory:" database to
    # whichever session happens to open next.
    eng = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncSession:
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def client(session_factory: async_sessionmaker) -> FakeClient:
    session = FakeTelegramSession()
    bot = Bot(token="123456:FAKE", session=session)
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_factory))
    dp.include_router(build_router())

    yield FakeClient(bot, dp, session)

    await bot.session.close()
