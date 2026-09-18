import structlog
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.tasks import TaskAction, TaskPageNav, render_task_page, task_page_keyboard
from bot.services.errors import TaskNotFoundError
from bot.services.task_service import TaskService

logger = structlog.get_logger()


async def _refresh_task_list(query: CallbackQuery, task_service: TaskService, page: int) -> None:
    """Re-render the task list in place after a done/delete action.

    query.message can be an InaccessibleMessage (too old to edit) instead of
    a real Message — in that case we just skip the edit instead of raising.
    """
    if not isinstance(query.message, Message):
        return

    task_page = await task_service.list_page(user_id=query.from_user.id, page=page)
    await query.message.edit_text(
        render_task_page(task_page), reply_markup=task_page_keyboard(task_page)
    )


async def cb_done(
    query: CallbackQuery, callback_data: TaskAction, task_service: TaskService
) -> None:
    try:
        task = await task_service.complete_task(
            user_id=query.from_user.id, task_id=callback_data.task_id
        )
    except TaskNotFoundError:
        await query.answer(f"Задача #{callback_data.task_id} не найдена", show_alert=True)
        return

    logger.info("task_completed", user_id=query.from_user.id, task_id=task.id)
    await query.answer("Готово ✅")
    await _refresh_task_list(query, task_service, page=callback_data.page)


async def cb_delete(
    query: CallbackQuery, callback_data: TaskAction, task_service: TaskService
) -> None:
    try:
        await task_service.delete_task(user_id=query.from_user.id, task_id=callback_data.task_id)
    except TaskNotFoundError:
        await query.answer(f"Задача #{callback_data.task_id} не найдена", show_alert=True)
        return

    logger.info("task_deleted", user_id=query.from_user.id, task_id=callback_data.task_id)
    await query.answer("Удалено 🗑")
    await _refresh_task_list(query, task_service, page=callback_data.page)


async def cb_page_nav(
    query: CallbackQuery, callback_data: TaskPageNav, task_service: TaskService
) -> None:
    await query.answer()
    await _refresh_task_list(query, task_service, page=callback_data.page)


def build_router() -> Router:
    router = Router(name="callbacks")
    router.callback_query.register(cb_done, TaskAction.filter(F.action == "done"))
    router.callback_query.register(cb_delete, TaskAction.filter(F.action == "delete"))
    router.callback_query.register(cb_page_nav, TaskPageNav.filter())
    return router
