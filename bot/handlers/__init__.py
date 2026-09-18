from aiogram import Router

from bot.handlers import callbacks, start, tasks

router = Router(name="root")
router.include_router(start.router)
router.include_router(tasks.router)
router.include_router(callbacks.router)

__all__ = ["router"]
