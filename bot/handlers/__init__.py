from aiogram import Router

from bot.handlers import callbacks, start, tasks


def build_router() -> Router:
    """A fresh router tree each call.

    aiogram routers can only ever be attached to one parent, so returning a
    module-level singleton here would blow up the moment a second
    Dispatcher — e.g. one created per test — tried to include it.
    """
    router = Router(name="root")
    router.include_router(start.build_router())
    router.include_router(tasks.build_router())
    router.include_router(callbacks.build_router())
    return router


__all__ = ["build_router"]
