from aiogram import Router

from bot.handlers import start, tasks

router = Router(name="root")
router.include_router(start.router)
router.include_router(tasks.router)

__all__ = ["router"]
