from html import escape

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.schemas.task import TaskPage


class TaskAction(CallbackData, prefix="task"):
    action: str  # "done" | "delete"
    task_id: int
    page: int  # page to re-render after the action, so the user isn't bounced to page 1


class TaskPageNav(CallbackData, prefix="taskpage"):
    page: int


def render_task_page(page: TaskPage) -> str:
    if not page.items:
        return "Активных задач нет 🎉"

    # Messages are sent with parse_mode=HTML (see bot/main.py) — task titles
    # are user-controlled text, not markup, so they must be escaped. Without
    # this, a title containing "<" (e.g. "<b>" or a stray "<") makes Telegram
    # reject the render with "can't parse entities" on every single re-render
    # of this list until the offending task is removed some other way.
    lines = [f"#{t.id} {escape(t.title)}" for t in page.items]
    lines.append(f"\nСтраница {page.page}/{page.total_pages}")
    return "\n".join(lines)


def task_page_keyboard(page: TaskPage) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for task in page.items:
        builder.button(
            text=f"✅ #{task.id}",
            callback_data=TaskAction(action="done", task_id=task.id, page=page.page),
        )
        builder.button(
            text=f"🗑 #{task.id}",
            callback_data=TaskAction(action="delete", task_id=task.id, page=page.page),
        )
    builder.adjust(2)

    nav_buttons = []
    if page.page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️", callback_data=TaskPageNav(page=page.page - 1).pack())
        )
    if page.page < page.total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="▶️", callback_data=TaskPageNav(page=page.page + 1).pack())
        )
    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()
