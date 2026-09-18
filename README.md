# Telegram Task Bot

A personal task-tracker Telegram bot. Python 3.12, aiogram 3, PostgreSQL,
SQLAlchemy async, Alembic, Docker, GitHub Actions CI.

## Features

- `/start` — register (idempotent, safe to send more than once)
- `/newtask <title>` — create a task
- `/tasks` — list your active tasks, 5 per page
- `/done <id>` / `/delete <id>` — act on a task by id, or use the inline
  ✅ / 🗑 buttons attached to each task in `/tasks`
- ◀️ / ▶️ inline pagination
- Every user only ever sees and can act on their own tasks — enforced at
  the repository layer, not just in the UI

## Architecture

```
bot/
  main.py          entrypoint: Bot + Dispatcher wiring, graceful shutdown
  core/             config (pydantic-settings) and structlog setup
  models/           SQLAlchemy models — User, Task
  schemas/          Pydantic I/O schemas (validation, serialization)
  repositories/      DB access — BaseRepository[ModelT] + UserRepository/TaskRepository
  services/         business logic — pagination, ownership checks
  middlewares/       DbSessionMiddleware: opens one DB session per update
  keyboards/        inline keyboard builders + CallbackData factories
  handlers/         command and callback handlers (thin — delegate to services)
```

Standard layering: `handlers` depend on `services`, `services` depend on
`repositories`, `repositories` depend on `models`. `schemas` are the
boundary type for anything crossing into/out of a service. This mirrors the
layout of [task-tracker-api](https://github.com/Nightroudt/task-tracker-api)
(same `BaseRepository[ModelT]` generic-repository pattern), adapted to
aiogram instead of FastAPI.

Two layers exist beyond the ones named in the spec, because aiogram needs
them:

- **`middlewares/`** — aiogram has no FastAPI-style `Depends()`.
  `DbSessionMiddleware` opens an `AsyncSession` per incoming update, builds
  `UserService`/`TaskService` from it, and injects them into the handler's
  kwargs by name — the same shape as a FastAPI dependency, just wired by
  hand.
- **`keyboards/`** — inline keyboards and their `CallbackData` payloads are
  presentation, not business logic, and they're shared between the initial
  `/tasks` reply and the callback handlers that re-render the list in place
  — they don't belong under `handlers/` or `services/`.

### Testing without a real Telegram server

aiogram has no official test client. The pattern used here (see
`tests/integration/fake_telegram.py`): subclass `BaseSession` and override
`make_request()` to return canned results instead of calling the real Bot
API, then drive it with `Bot(session=FakeTelegramSession())` and
`Dispatcher.feed_update(bot, update)`. This exercises the real
middleware → handler → service → repository chain, including inline
keyboards and callback queries, entirely offline.

- `tests/unit/` — `TaskService`/`UserService` against mocked repositories
- `tests/integration/test_repositories.py` — repositories against a real
  (in-memory SQLite) database
- `tests/integration/test_handlers.py` — full command/callback flows via
  the fake aiogram session, including cross-user ownership checks and
  pagination edge cases (e.g. deleting the last task on the last page
  correctly bounces back to page 1)

## Running locally

```bash
python -m venv .venv
.venv/Scripts/activate  # or source .venv/bin/activate on Linux/macOS
pip install -r requirements-dev.txt

cp .env.example .env  # fill in BOT_TOKEN from @BotFather, and a real DATABASE_URL

alembic upgrade head
python -m bot.main
```

## Running with Docker Compose

```bash
cp .env.example .env  # fill in BOT_TOKEN
docker compose up --build
```

This starts PostgreSQL and the bot together; `docker-entrypoint.sh` runs
`alembic upgrade head` before the bot starts polling, so the schema is
always up to date on container start.

## Tests

```bash
ruff check .
pytest -v
```

No Docker or PostgreSQL needed — the whole suite runs against in-memory
SQLite and the fake aiogram session described above.
