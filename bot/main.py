import asyncio

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.core.config import settings
from bot.core.logging import configure_logging
from bot.handlers import build_router
from bot.middlewares import DbSessionMiddleware

logger = structlog.get_logger()


async def main() -> None:
    configure_logging(settings.log_level)

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_factory))
    dp.include_router(build_router())

    async def on_shutdown() -> None:
        logger.info("shutting_down")
        await engine.dispose()

    dp.shutdown.register(on_shutdown)

    logger.info("bot_starting")
    try:
        await dp.start_polling(bot)
    finally:
        # dp.start_polling runs dp.shutdown hooks (which disposes the engine
        # above) in its own `finally` before returning here, on every
        # platform — on Linux/macOS via its SIGINT/SIGTERM handler cleanly
        # stopping the polling loop first; on Windows, where asyncio can't
        # register a signal handler at all, via a plain KeyboardInterrupt
        # propagating through that same `finally` (verified empirically:
        # the hook still runs, just without the graceful in-flight-task
        # drain the signal-handler path gets). Either way, this line just
        # closes the bot's own HTTP session on the way out.
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
