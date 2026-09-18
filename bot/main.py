import asyncio

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.core.config import settings
from bot.core.logging import configure_logging
from bot.handlers import router as root_router
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
    dp.include_router(root_router)

    async def on_shutdown() -> None:
        logger.info("shutting_down")
        await engine.dispose()

    dp.shutdown.register(on_shutdown)

    logger.info("bot_starting")
    try:
        await dp.start_polling(bot)
    finally:
        # dp.start_polling already handles SIGINT/SIGTERM by cancelling its
        # own polling task and running dp.shutdown hooks (which disposes the
        # engine above) before returning here — this just closes the bot's
        # own HTTP session on the way out.
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
