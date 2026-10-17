# Прогресс разработки

Источник требований: `tech/tech-1.md`, версия 1.2.

| Слайс | Статус |
| --- | --- |
| 1. Инфраструктурный каркас | REVIEW_REQUIRED |
| 2. Справочники тарифов и промокодов | ACCEPTED |
| 3. Модель платежа и график рассрочки | REVIEW_REQUIRED |
| 4. Pydantic-контракты платежей | ACCEPTED |
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

## Слайс 2

Завершён технически 2026-10-17. Принят пользователем после проверки
работы маршрута, начальных записей в БД и формата ответа.
Статус слайса 1 не изменён.

### Изменённые и созданные файлы

- `src/kvitto_test/models/tariff.py`, `src/kvitto_test/models/promo_code.py`,
  `src/kvitto_test/models/__init__.py` — ORM-модели справочников и ограничения.
- `src/kvitto_test/domain/__init__.py`, `src/kvitto_test/domain/tariff.py` —
  независимое от ORM представление тарифа.
- `src/kvitto_test/application/__init__.py`,
  `src/kvitto_test/application/tariffs.py` — контракт чтения тарифов и сценарий
  получения списка.
- `src/kvitto_test/repositories/__init__.py`,
  `src/kvitto_test/repositories/tariff.py` — чтение тарифов из PostgreSQL через
  AsyncSession.
- `src/kvitto_test/schemas/__init__.py`, `src/kvitto_test/schemas/tariff.py` —
  HTTP-схема TariffResponse.
- `src/kvitto_test/api/routes/__init__.py`,
  `src/kvitto_test/api/routes/tariffs.py`, `src/kvitto_test/api/router.py` —
  маршрут `GET /tariffs`.
- `alembic/env.py`, `alembic/versions/20261017_01_create_references.py` —
  регистрация моделей, миграция таблиц и начальные данные.
- `tech/PROGRESS.md` — учёт состояния слайса.

### Архитектурные решения

- ORM-модели остаются в инфраструктуре; репозиторий преобразует строки БД в
  независимые от SQLAlchemy объекты. API вызывает application-сценарий и
  преобразует результат в Pydantic-схему.
- Начальные тарифы и `KVITTO10` создаются миграцией с фиксированными UUID;
  повторное применение к новой БД даёт те же записи. `created_at` и `is_active`
  задаются серверными значениями по умолчанию.
- Денежные суммы хранятся как `BIGINT` и передаются как `int`/JSON integer.
  Бизнес-логика промокода и платежей не реализована по плану следующих слайсов.

### Ручные проверки

- `uv run --no-sync --offline python -m compileall -q src/kvitto_test alembic`: успешно.
- Импорт приложения и моделей: успешно; в metadata зарегистрированы `tariffs`
  и `promo_codes`.
- OpenAPI: `GET /tariffs` имеет ответ 200 в виде массива `TariffResponse`
  с полями `id`, `title`, `price`.
- После замечания пользователя в маршруте явно задан `status_code=200`;
  ручной запрос через ASGI-клиент с пустым источником тарифов вернул HTTP 200
  и `[]`.
- `uv run --no-sync --offline alembic history`: новая ревизия является head.
- `uv run --no-sync --offline alembic upgrade --sql head`: успешно сгенерированы
  таблицы, ограничения и вставки всех четырёх начальных записей.
- После форматирования файлов слайса: Python-строки не превышают 88 символов,
  нет завершающих пробелов и отсутствующих переводов строки в конце файлов;
  повторная компиляция Python прошла успешно. `git diff --check` для затронутых
  отслеживаемых файлов не выявил ошибок.

Для команд `uv` использовался `UV_CACHE_DIR` внутри проекта из-за отказа доступа
к пользовательскому кэшу. Агент не проверял миграцию и `GET /tariffs` на
работающей PostgreSQL: подключение к БД не предоставлено. Пользователь
подтвердил создание записей в БД, работу маршрута и корректный формат ответа.
Автоматические тесты не создавались.

## Слайс 3

Технически завершён 2026-10-17. Ожидает проверки пользователя.

### Изменённые и созданные файлы

- `src/kvitto_test/domain/payment.py` — значения способов оплаты и статусов.
- `src/kvitto_test/schemas/enums.py` — экспорт Enum для будущих HTTP-схем.
- `src/kvitto_test/models/payment.py` — ORM-модель платежа и ограничения.
- `src/kvitto_test/models/payment_installment.py` — ORM-модель взноса рассрочки.
- `src/kvitto_test/models/tariff.py`, `src/kvitto_test/models/promo_code.py`,
  `src/kvitto_test/models/__init__.py` — двусторонние связи и регистрация моделей.
- `alembic/versions/20261017_02_create_payments.py` — миграция новых таблиц.
- `tech/PROGRESS.md` — статус и описание слайса.

### Архитектурные решения

- Enum определены в доменном модуле, чтобы ORM не зависела от HTTP-слоя;
  `schemas/enums.py` предоставляет их для будущих Pydantic-контрактов.
- Денежные поля хранятся как `BIGINT`, а допустимые значения, положительные
  суммы и уникальность ключа идемпотентности защищены ограничениями БД.
- `status`, `created_at` и `updated_at` имеют серверные значения по умолчанию;
  при обновлении через ORM `updated_at` получает текущее время.

### Ручные проверки

- Импорт ORM-моделей и `configure_mappers()` прошли успешно; metadata содержит
  четыре таблицы.
- `uv run --no-sync --offline alembic history`: новая ревизия является head.
- `uv run --no-sync --offline alembic upgrade --sql 20261017_01:head`:
  SQL для таблиц, внешних ключей и CHECK-ограничений сгенерирован успешно.
- `uv run --no-sync --offline python -m compileall -q src/kvitto_test alembic`:
  успешно.

Миграция на работающей PostgreSQL не применялась в рамках проверки.
Создание платежей, расчёт рассрочки, переходы статусов и HTTP-схемы платежей
относятся к следующим этапам. Автоматические тесты не создавались. Коммит
не создавался.

По просьбе пользователя временно удалённые импорты под `TYPE_CHECKING`
возвращены: без них IDE сообщает об ошибках в аннотациях связей. Статус
слайса остаётся `REVIEW_REQUIRED`.

## Слайс 4

Технически завершён и принят пользователем 2026-10-17.

### Созданные и изменённые файлы

- `src/kvitto_test/schemas/payment.py` — входная схема создания платежа и схема ответа.
- `src/kvitto_test/schemas/webhook.py` — схемы запроса, успешного ответа и ошибки перехода статуса.
- `tech/PROGRESS.md` — статус и описание слайса.

### Архитектурные решения

- HTTP-схемы используют уже определённые доменные Enum, не связывая домен с Pydantic.
- `installment_months` допускает только 3, 6 или 12 для рассрочки; для остальных
  способов оплаты поле должно отсутствовать или быть `null`.
- В `PaymentResponse` поля `installment_months` и `schedule` обязательны в структуре
  ответа и допускают `null`. Денежные поля имеют тип `int`.

### Ручные проверки

- `uv run --no-sync --offline python -m compileall -q src/kvitto_test/schemas`: успешно.
- Вручную проверены допустимые и недопустимые сочетания способа оплаты и срока,
  запрет дополнительных полей, сериализация денежных сумм и nullable-полей,
  создание webhook-схем: успешно.

Маршруты платежей, работа с БД и бизнес-логика не реализованы в этом слайсе.
Автоматические тесты не создавались. Миграции не требуются.
