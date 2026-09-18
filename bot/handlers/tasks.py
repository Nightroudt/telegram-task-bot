from html import escape

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
    except ValidationError as exc:
        if any(err["type"] == "string_too_long" for err in exc.errors()):
            await message.answer("Название задачи слишком длинное (максимум 255 символов).")
        else:
            await message.answer("Название задачи не может быть пустым.")
        return

    task = await task_service.create_task(user_id=message.from_user.id, title=data.title)
    logger.info("task_created", user_id=message.from_user.id, task_id=task.id)
    await message.answer(f"Задача #{task.id} «{escape(task.title)}» создана.")


async def cmd_tasks(message: Message, task_service: TaskService) -> None:
    if message.from_user is None:
        return

    page = await task_service.list_page(user_id=message.from_user.id, page=1)
    await message.answer(render_task_page(page), reply_markup=task_page_keyboard(page))


# tasks.id is a Postgres int4 column; anything outside this range would
# overflow asyncpg's encoder with an unhandled error instead of a clean
# "not found" reply.
_MAX_TASK_ID = 2_147_483_647


async def _parse_task_id(message: Message, command: CommandObject) -> int | None:
    usage = f"Использование: /{command.command} <id> (число, см. /tasks)"

    if command.args is None:
        await message.answer(usage)
        return None

    try:
        # str.isdigit() is not a safe pre-check here: it accepts non-ASCII
        # "digit" characters (e.g. superscript ²) that int() then rejects.
        task_id = int(command.args.strip())
    except ValueError:
        await message.answer(usage)
        return None

    if not (1 <= task_id <= _MAX_TASK_ID):
        await message.answer(usage)
        return None

    return task_id


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
    await message.answer(f"Задача #{task.id} «{escape(task.title)}» отмечена выполненной ✅")


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
