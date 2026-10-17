# Прогресс разработки

Источник требований: `tech/tech-1.md`, версия 1.2.

| Слайс | Статус |
| --- | --- |
| 1. Инфраструктурный каркас | REVIEW_REQUIRED |
| 2. Справочники тарифов и промокодов | PENDING |
| 3. Модель платежа и график рассрочки | PENDING |
| 4. Pydantic-контракты платежей | PENDING |
| 5. Каркас эндпойнтов платежей и webhook | PENDING |

## Слайс 1

Завершён технически 2026-10-17. Ожидает проверки пользователя. `tech/PROGRESS.md` ранее отсутствовал.

### Изменённые и созданные файлы

- `.gitignore`, `pyproject.toml`, `uv.lock`, `README.md` — зависимости, игнорирование локального кэша `uv`, команда запуска.
- `.env.example` — пример конфигурации PostgreSQL.
- `src/kvitto_test/main.py`, `src/kvitto_test/api/__init__.py`, `src/kvitto_test/api/router.py` — FastAPI и корневой роутер.
- `src/kvitto_test/core/__init__.py`, `src/kvitto_test/core/config.py`, `src/kvitto_test/core/database.py` — Pydantic Settings, асинхронные engine и фабрика сессий.
- `src/kvitto_test/models/__init__.py`, `src/kvitto_test/models/base.py` — общий declarative base без таблиц.
- `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, `alembic/versions/.gitkeep` — окружение будущих миграций.
- `tech/PROGRESS.md` — учёт состояния слайсов.

### Архитектурные решения

- Использован существующий пакет `kvitto_test`, поэтому рабочая команда запуска: `uv run uvicorn kvitto_test.main:app --reload`. Упоминание `app.main` в разделе результата ТЗ расходится с указанной в нём же структурой `src/kvitto_test`.
- Подключение к БД создаётся асинхронным SQLAlchemy, сессии выдаются через `get_session` без неявного `commit`.
- Alembic использует `Base.metadata` и `DATABASE_URL` из настроек; модели и миграции таблиц относятся к следующим слайсам.

### Ручные проверки

- `uv run python --version`: Python 3.11.1.
- `uv sync --locked --offline`: успешно.
- Импорт приложения, engine, фабрики сессий и metadata: успешно, PostgreSQL dialect, 0 таблиц.
- Запрос `GET /docs` через ASGI-клиент: HTTP 200, Swagger UI присутствует.
- Запуск `uv run uvicorn kvitto_test.main:app --host 127.0.0.1 --port 8765` и запрос `GET /docs` по HTTP: приложение запустилось, получен HTTP 200.
- `uv run alembic history` и `uv run alembic upgrade --sql head`: успешно; ревизий пока нет.
- `uv run python -m compileall -q src/kvitto_test alembic`: успешно.
- `git diff --check`: без ошибок; Git сообщил только о возможной нормализации окончаний строк.

Реальное подключение к PostgreSQL не проверялось: работающая база не предоставлена. API тарифов и платежей, ORM-таблицы и бизнес-логика пока не реализованы по плану следующих слайсов. Коммиты не создавались.
