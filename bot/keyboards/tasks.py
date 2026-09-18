from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.schemas.task import TaskPage


class TaskAction(CallbackData, prefix="task"):
    action: str  # "done" | "delete"
    task_id: int


def render_task_page(page: TaskPage) -> str:
    if not page.items:
        return "Активных задач нет 🎉"

    lines = [f"#{t.id} {t.title}" for t in page.items]
    lines.append(f"\nСтраница {page.page}/{page.total_pages}")
    return "\n".join(lines)


def task_page_keyboard(page: TaskPage) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for task in page.items:
        builder.button(
            text=f"✅ #{task.id}", callback_data=TaskAction(action="done", task_id=task.id)
        )
        builder.button(
            text=f"🗑 #{task.id}", callback_data=TaskAction(action="delete", task_id=task.id)
        )
    builder.adjust(2)
    return builder.as_markup()
