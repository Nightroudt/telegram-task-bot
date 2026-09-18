import structlog
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from pydantic import ValidationError

from bot.keyboards.tasks import render_task_page, task_page_keyboard
from bot.schemas.task import TaskCreate
from bot.services.errors import TaskNotFoundError
from bot.services.task_service import TaskService

logger = structlog.get_logger()


async def cmd_newtask(
    message: Message, command: CommandObject, task_service: TaskService
) -> None:
    if message.from_user is None:
        return

    if command.args is None:
        await message.answer("Использование: /newtask <название задачи>")
        return

    try:
        data = TaskCreate(title=command.args)
    except ValidationError:
        await message.answer("Название задачи не может быть пустым.")
        return

    task = await task_service.create_task(user_id=message.from_user.id, title=data.title)
    logger.info("task_created", user_id=message.from_user.id, task_id=task.id)
    await message.answer(f"Задача #{task.id} «{task.title}» создана.")


async def cmd_tasks(message: Message, task_service: TaskService) -> None:
    if message.from_user is None:
        return

    page = await task_service.list_page(user_id=message.from_user.id, page=1)
    await message.answer(render_task_page(page), reply_markup=task_page_keyboard(page))


async def _parse_task_id(message: Message, command: CommandObject) -> int | None:
    if command.args is None or not command.args.strip().isdigit():
        await message.answer(f"Использование: /{command.command} <id> (число, см. /tasks)")
        return None
    return int(command.args.strip())


async def cmd_done(message: Message, command: CommandObject, task_service: TaskService) -> None:
    if message.from_user is None:
        return

    task_id = await _parse_task_id(message, command)
    if task_id is None:
        return

    try:
        task = await task_service.complete_task(user_id=message.from_user.id, task_id=task_id)
    except TaskNotFoundError:
        await message.answer(f"Задача #{task_id} не найдена.")
        return

    logger.info("task_completed", user_id=message.from_user.id, task_id=task.id)
    await message.answer(f"Задача #{task.id} «{task.title}» отмечена выполненной ✅")


async def cmd_delete(message: Message, command: CommandObject, task_service: TaskService) -> None:
    if message.from_user is None:
        return

    task_id = await _parse_task_id(message, command)
    if task_id is None:
        return

    try:
        await task_service.delete_task(user_id=message.from_user.id, task_id=task_id)
    except TaskNotFoundError:
        await message.answer(f"Задача #{task_id} не найдена.")
        return

    logger.info("task_deleted", user_id=message.from_user.id, task_id=task_id)
    await message.answer(f"Задача #{task_id} удалена.")


def build_router() -> Router:
    router = Router(name="tasks")
    router.message.register(cmd_newtask, Command("newtask"))
    router.message.register(cmd_tasks, Command("tasks"))
    router.message.register(cmd_done, Command("done"))
    router.message.register(cmd_delete, Command("delete"))
    return router
