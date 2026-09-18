from bot.keyboards.tasks import TaskAction, TaskPageNav
from tests.integration.fake_telegram import FakeClient


def keyboard_texts(method) -> list[str]:
    if not method.reply_markup:
        return []
    return [b.text for row in method.reply_markup.inline_keyboard for b in row]


async def test_start_registers_user_and_greets_them(client: FakeClient) -> None:
    reply = await client.send(777, "/start")

    assert "Привет" in reply.text
    assert "/newtask" in reply.text


async def test_start_is_idempotent(client: FakeClient) -> None:
    first = await client.send(777, "/start")
    second = await client.send(777, "/start")

    assert first.text == second.text


async def test_newtask_creates_a_task(client: FakeClient) -> None:
    await client.send(777, "/start")

    reply = await client.send(777, "/newtask Buy milk")

    assert "Buy milk" in reply.text
    assert "#1" in reply.text


async def test_newtask_rejects_blank_title(client: FakeClient) -> None:
    await client.send(777, "/start")

    reply = await client.send(777, "/newtask")

    assert "Использование" in reply.text


async def test_tasks_lists_active_tasks_with_inline_keyboard(client: FakeClient) -> None:
    await client.send(777, "/start")
    await client.send(777, "/newtask Buy milk")

    reply = await client.send(777, "/tasks")

    assert "Buy milk" in reply.text
    assert "✅ #1" in keyboard_texts(reply)
    assert "🗑 #1" in keyboard_texts(reply)


async def test_done_command_marks_task_completed_and_removes_from_list(
    client: FakeClient,
) -> None:
    await client.send(777, "/start")
    await client.send(777, "/newtask Buy milk")

    done_reply = await client.send(777, "/done 1")
    list_reply = await client.send(777, "/tasks")

    assert "выполненной" in done_reply.text
    assert "Активных задач нет" in list_reply.text


async def test_done_command_reports_missing_task(client: FakeClient) -> None:
    await client.send(777, "/start")

    reply = await client.send(777, "/done 999")

    assert "не найдена" in reply.text


async def test_delete_command_removes_task(client: FakeClient) -> None:
    await client.send(777, "/start")
    await client.send(777, "/newtask Buy milk")

    delete_reply = await client.send(777, "/delete 1")
    list_reply = await client.send(777, "/tasks")

    assert "удалена" in delete_reply.text
    assert "Активных задач нет" in list_reply.text


async def test_a_user_cannot_delete_someone_elses_task_via_command(client: FakeClient) -> None:
    await client.send(777, "/start")
    await client.send(777, "/newtask Owner's task")
    await client.send(888, "/start")

    reply = await client.send(888, "/delete 1")

    assert "не найдена" in reply.text
    still_there = await client.send(777, "/tasks")
    assert "Owner's task" in still_there.text


async def test_done_via_inline_button(client: FakeClient) -> None:
    await client.send(777, "/start")
    await client.send(777, "/newtask Buy milk")

    reply = await client.click(777, TaskAction(action="done", task_id=1, page=1).pack())

    assert "Активных задач нет" in reply.text


async def test_a_user_cannot_act_on_someone_elses_task_via_forged_callback(
    client: FakeClient,
) -> None:
    await client.send(777, "/start")
    await client.send(777, "/newtask Owner's task")
    await client.send(888, "/start")

    reply = await client.click(888, TaskAction(action="delete", task_id=1, page=1).pack())

    assert reply.text == "Задача не найдена"
    still_there = await client.send(777, "/tasks")
    assert "Owner's task" in still_there.text


async def test_pagination_navigation_between_pages(client: FakeClient) -> None:
    await client.send(777, "/start")
    for i in range(1, 8):  # PAGE_SIZE=5 -> page 1 has 5, page 2 has 2
        await client.send(777, f"/newtask Task {i}")

    page1 = await client.send(777, "/tasks")
    assert "Страница 1/2" in page1.text
    assert "▶️" in keyboard_texts(page1)
    assert "◀️" not in keyboard_texts(page1)

    page2 = await client.click(777, TaskPageNav(page=2).pack())
    assert "Страница 2/2" in page2.text
    assert "◀️" in keyboard_texts(page2)
    assert "▶️" not in keyboard_texts(page2)

    back_to_page1 = await client.click(777, TaskPageNav(page=1).pack())
    assert "Страница 1/2" in back_to_page1.text


async def test_pagination_clamps_back_after_emptying_last_page(client: FakeClient) -> None:
    await client.send(777, "/start")
    for i in range(1, 8):
        await client.send(777, f"/newtask Task {i}")
    await client.click(777, TaskPageNav(page=2).pack())

    await client.click(777, TaskAction(action="delete", task_id=6, page=2).pack())
    last_reply = await client.click(777, TaskAction(action="delete", task_id=7, page=2).pack())

    assert "Страница 1/1" in last_reply.text
