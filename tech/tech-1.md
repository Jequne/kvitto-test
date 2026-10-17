# Техническое задание
## Каркас платёжного API на FastAPI — вертикальные слайсы

**Версия:** 1.2  
**Стек:** Python 3.11, uv, FastAPI, Pydantic v2, SQLAlchemy 2.0, PostgreSQL, Alembic  
**Текущая цель:** Создать архитектурный каркас приложения без бизнес-логики и тестов.

---

# 1. Общие требования

Разработать базовую структуру REST API для системы платежей, тарифов, промокодов и рассрочек.

Проект уже инициализирован командой `uv init`. Необходимо продолжать разработку внутри существующего проекта.

Запрещается повторно инициализировать проект, без необходимости перезаписывать `pyproject.toml` или заменять менеджер зависимостей.

На текущем этапе необходимо:

- Организовать структуру приложения.
- Создать ORM-модели и связи.
- Создать Pydantic-схемы.
- Определить Enum и типы данных.
- Подготовить PostgreSQL и миграции Alembic.
- Создать маршруты FastAPI.
- Объявить HTTP-контракты.
- Предусмотреть точки расширения для будущей бизнес-логики.

Не реализовывать бизнес-логику и автоматические тесты.

**Основной принцип:** выполнение строго по слайсам. После каждого слайса остановиться, предоставить результат и дождаться подтверждения перед переходом к следующему.

---

# 2. Денежные суммы

Все денежные суммы должны выражаться целым числом копеек.

| Уровень | Тип |
|---|---|
| PostgreSQL | BIGINT |
| SQLAlchemy | BigInteger |
| Python | int |
| Pydantic | int |
| JSON | integer |

Не использовать `float` для денежных значений.

Исходные тарифы:

| Код | Цена в копейках |
|---|---:|
| `basic` | 990000 |
| `standard` | 1990000 |
| `premium` | 2990000 |

При последующем расчёте процентных скидок допускается использование `Decimal` для промежуточной точной арифметики. Сохраняемые значения должны оставаться целыми копейками.

---

# 3. Контракты предметной области

## Тарифы

Тариф имеет идентификатор, код, название и стоимость.

## Промокоды

Исходный промокод `KVITTO10` предоставляет скидку 10%. Регистр кода не имеет значения. Неизвестный промокод должен приводить к HTTP 422.

## Способы оплаты

`PaymentMethod`:

- `card`
- `sbp`
- `installment`

Для `installment` срок обязателен. Допустимые значения: 3, 6 или 12 месяцев.

## Статусы

`PaymentStatus`:

- `pending`
- `succeeded`
- `failed`
- `refunded`

Новый платёж создаётся со статусом `pending`.

Допустимые переходы:

```text
pending -> succeeded
pending -> failed
succeeded -> refunded
```

Проверка этих переходов будет реализована позднее.

## Рассрочка

График рассрочки представляет собой список целых сумм в копейках.

Сумма элементов графика должна быть равна итоговой сумме платежа. Остаток распределяется между первыми платежами.

Пример:

```python
amount = 1990000
schedule = [663334, 663333, 663333]
```

Даты взносов не требуются.

---

# 4. План реализации

## Слайс 1. Инфраструктурный каркас

**Цель:** подготовить существующий uv-проект к работе как FastAPI-приложение с PostgreSQL.

### Реализовать

1. Проверить существующий `pyproject.toml`.
2. Настроить Python 3.11 с совместимым `requires-python`.
3. Установить необходимые зависимости через `uv add`.
4. Создать основной пакет `app`.
5. Настроить конфигурацию через Pydantic Settings.
6. Настроить асинхронный SQLAlchemy Engine.
7. Создать фабрику асинхронных сессий.
8. Создать FastAPI-приложение и корневой APIRouter.
9. Подготовить подключение Alembic к metadata SQLAlchemy.

### Зависимости

```bash
uv add fastapi "uvicorn[standard]" sqlalchemy asyncpg alembic pydantic-settings email-validator
```

### Файлы

```text
app/
├── __init__.py
├── main.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   └── database.py
├── models/
│   ├── __init__.py
│   └── base.py
└── api/
    ├── __init__.py
    └── router.py

.env.example
alembic.ini
alembic/
├── env.py
└── versions/
```

### Результат

- Приложение запускается через `uv run uvicorn app.main:app --reload`.
- Swagger UI доступен по `/docs`.
- Конфигурация PostgreSQL считывается из переменных окружения.
- Асинхронный Engine и SessionFactory созданы.
- Alembic настроен для последующих миграций.

**После выполнения остановиться и показать результат.**

---

## Слайс 2. Справочники тарифов и промокодов

**Цель:** сформировать первый законченный фрагмент предметной области — справочники и контракт получения тарифов.

### ORM-модель Tariff

Таблица `tariffs`:

| Поле | PostgreSQL | Ограничения |
|---|---|---|
| id | UUID | PK |
| code | VARCHAR(32) | UNIQUE, NOT NULL |
| title | VARCHAR(100) | NOT NULL |
| price | BIGINT | NOT NULL, > 0 |
| created_at | TIMESTAMPTZ | NOT NULL |

### ORM-модель PromoCode

Таблица `promo_codes`:

| Поле | PostgreSQL | Ограничения |
|---|---|---|
| id | UUID | PK |
| code | VARCHAR(64) | UNIQUE, NOT NULL |
| discount_percent | SMALLINT | NOT NULL, от 0 до 100 |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE |
| created_at | TIMESTAMPTZ | NOT NULL |

### Pydantic-схема TariffResponse

| Поле | Тип |
|---|---|
| id | UUID |
| title | str |
| price | int |

Установить `ConfigDict(from_attributes=True)`.

### Эндпойнт

`GET /tariffs`

Успешный ответ:

- HTTP 200
- `response_model=list[TariffResponse]`

### Дополнительно

Подготовить начальную миграцию справочников и воспроизводимое заполнение данными:

```text
basic     990000
standard  1990000
premium   2990000

KVITTO10  10%
```

Создать возможность получения тарифов из PostgreSQL без реализации платёжной логики.

### Файлы

```text
app/models/tariff.py
app/models/promo_code.py
app/schemas/tariff.py
app/api/routes/tariffs.py
app/repositories/tariff.py
```

### Результат

Созданы таблицы и Pydantic-схема тарифа, а `GET /tariffs` получает данные из базы в объявленном формате.

**После выполнения остановиться и показать результат.**

---

## Слайс 3. Модель платежа и график рассрочки

**Цель:** создать структуру хранения платежей с необходимыми связями, статусами, денежными полями и будущей поддержкой идемпотентности.

### Enum

Определить:

```python
class PaymentMethod(str, Enum):
    CARD = "card"
    SBP = "sbp"
    INSTALLMENT = "installment"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
```

### ORM-модель Payment

Таблица `payments`:

| Поле | PostgreSQL | Ограничения |
|---|---|---|
| id | UUID | PK |
| tariff_id | UUID | FK, NOT NULL |
| promo_code_id | UUID | FK, NULL |
| email | VARCHAR(254) | NOT NULL |
| method | VARCHAR(20) | NOT NULL |
| status | VARCHAR(20) | NOT NULL, DEFAULT pending |
| amount | BIGINT | NOT NULL, > 0 |
| discount | BIGINT | NOT NULL, >= 0 |
| installment_months | SMALLINT | NULL |
| idempotency_key | VARCHAR(255) | UNIQUE, NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

`amount` — итоговая сумма к оплате, `discount` — абсолютная скидка, обе величины в копейках.

Ограничить `method`, `status` и `installment_months` допустимыми значениями через ограничения базы данных.

### ORM-модель PaymentInstallment

Таблица `payment_installments`:

| Поле | PostgreSQL | Ограничения |
|---|---|---|
| id | UUID | PK |
| payment_id | UUID | FK, NOT NULL |
| sequence | SMALLINT | NOT NULL, > 0 |
| amount | BIGINT | NOT NULL, > 0 |

Уникальная комбинация: `(payment_id, sequence)`.

### Связи

- Tariff → Payment: один ко многим.
- PromoCode → Payment: один ко многим.
- Payment → PaymentInstallment: один ко многим.

### Дополнительно

Создать миграцию таблиц платежей и рассрочек.

### Файлы

```text
app/schemas/enums.py
app/models/payment.py
app/models/payment_installment.py
```

### Результат

Сформирована структура хранения платежей, все отношения описаны через SQLAlchemy, ограничения PostgreSQL заданы, миграция подготовлена.

Не реализовывать создание платежа, расчёт рассрочки и переходы статусов.

**После выполнения остановиться и показать результат.**

---

## Слайс 4. Pydantic-контракты платежей

**Цель:** определить точные входные и выходные схемы API, не привязывая их к готовой бизнес-логике.

### PaymentCreateRequest

| Поле | Тип | Обязательность |
|---|---|---|
| tariff_id | UUID | Да |
| email | EmailStr | Да |
| method | PaymentMethod | Да |
| installment_months | Literal[3, 6, 12] \| None | Для рассрочки |
| promo_code | str \| None | Нет |

Добавить Pydantic-валидатор согласованности `method` и `installment_months`.

Запретить дополнительные поля через `extra="forbid"`.

### PaymentResponse

| Поле | Тип |
|---|---|
| id | UUID |
| status | PaymentStatus |
| tariff_id | UUID |
| amount | int |
| discount | int |
| method | PaymentMethod |
| installment_months | int \| None |
| schedule | list[int] \| None |
| email | EmailStr |
| created_at | datetime |

Nullable-поля присутствуют в ответе даже со значением `null`.

Все денежные значения сериализуются как целые JSON-числа.

### PaymentWebhookRequest

| Поле | Тип |
|---|---|
| payment_id | UUID |
| status | PaymentStatus |

### PaymentWebhookResponse

```python
result: Literal["ok"]
```

### InvalidTransitionResponse

```python
error: Literal["invalid_transition"]
```

### Файлы

```text
app/schemas/payment.py
app/schemas/webhook.py
```

### Результат

Все Pydantic-контракты подготовлены. Схемы можно использовать для FastAPI `response_model` и документирования HTTP-интерфейса.

Не реализовывать работу с базой в рамках этого слайса.

**После выполнения остановиться и показать результат.**

---

## Слайс 5. Каркас эндпойнтов платежей и webhook

**Цель:** зарегистрировать все оставшиеся маршруты и полностью определить HTTP-контракты.

### POST /payments

Request: `PaymentCreateRequest`.

Необязательный HTTP-заголовок `Idempotency-Key`.

Контракт:

| HTTP | Значение |
|---|---|
| 201 | Создан новый платёж |
| 200 | Возвращён существующий платёж при повторе ключа |
| 422 | Ошибка валидации или неизвестный промокод |

Успешный ответ: `PaymentResponse`.

### GET /payments/{id}

Параметр `id`: UUID.

Контракт:

| HTTP | Значение |
|---|---|
| 200 | Платёж найден |
| 404 | Платёж отсутствует |
| 422 | Некорректный UUID |

Успешный ответ: `PaymentResponse`.

### POST /webhooks/bank

Request: `PaymentWebhookRequest`.

Контракт:

| HTTP | Значение |
|---|---|
| 200 | Успешная обработка |
| 404 | Платёж не найден |
| 409 | Недопустимый переход |
| 422 | Ошибка валидации |

HTTP 200:

```json
{"result": "ok"}
```

HTTP 409:

```json
{"error": "invalid_transition"}
```

В `responses` FastAPI указать нестандартную модель ответа 409.

### Реализация

Создать APIRouter для платежей и webhook, зарегистрировать их в основном роутере приложения.

Создать интерфейсы будущих сервисов и зависимости только там, где они необходимы для определения структуры.

Пока операции не реализованы, использовать явные заглушки, например HTTP 501 Not Implemented. Не возвращать фиктивные успешные платежи.

### Файлы

```text
app/api/routes/payments.py
app/api/routes/webhooks.py
app/services/payment.py
app/services/webhook.py
```

### Результат

Все четыре маршрута приложения присутствуют в Swagger UI, их входные и выходные Pydantic-схемы, HTTP-статусы и форматы ошибок задокументированы.

Бизнес-логика отсутствует.

**После выполнения остановиться и показать результат.**

---

# 5. Итоговая структура проекта

Все изменения выполнять внутри уже созданного uv-проекта.

```text
kvitto-test/
├── .python-version
├── .venv/
├── .env
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
├── README.md
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── database.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── tariff.py
│   │   ├── promo_code.py
│   │   ├── payment.py
│   │   └── payment_installment.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── enums.py
│   │   ├── tariff.py
│   │   ├── payment.py
│   │   └── webhook.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── tariffs.py
│   │       ├── payments.py
│   │       └── webhooks.py
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── tariff.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── payment.py
│   │   └── webhook.py
│   │
│   └── dependencies/
│       ├── __init__.py
│       └── database.py
│
├── alembic/
│   ├── env.py
│   └── versions/
│
└── alembic.ini
```

Не создавать `tests/` и не добавлять зависимости для тестирования.

---

# 6. Правила выполнения слайсов

Работу выполнять строго последовательно.

После завершения каждого слайса необходимо:

1. Указать созданные и изменённые файлы.
2. Кратко описать принятые архитектурные решения.
3. Сообщить, какие компоненты реализованы, а какие пока являются заглушками.
4. Указать команды для локального запуска или применения миграций, если они требуются.
5. Остановиться и дождаться дальнейших указаний.

Не переходить автоматически к следующему слайсу.

Не реализовывать заранее функциональность последующих слайсов.

Не писать автоматические тесты, тестовые фикстуры и дополнительную тестовую инфраструктуру.

Не добавлять Redis, RabbitMQ, Celery, Docker или другие компоненты, которые не требуются текущими условиями.

Допускается минимальная ручная проверка запуска приложения, импорта модулей и корректности миграций, но без создания автоматизированных тестов.

---

# 7. Критерии завершения всего этапа

После выполнения пяти слайсов должен существовать работающий архитектурный каркас приложения.

Должны быть готовы:

- FastAPI-приложение с настроенным uv-окружением.
- Подключение к PostgreSQL через AsyncSession.
- Конфигурация через Pydantic Settings.
- Четыре ORM-модели с внешними ключами и ограничениями.
- Pydantic-схемы входных и выходных данных.
- Enum-типы способов оплаты и статусов.
- Миграции Alembic.
- Начальные записи тарифов и промокода.
- Четыре зарегистрированных API-эндпойнта.
- OpenAPI-документация с HTTP-контрактами.

Допускается отсутствие фактической обработки POST-запросов, если интерфейсы и заглушки корректно оформлены.

**После этого этап считается завершённым. Дальнейшая бизнес-логика и тестирование планируются отдельно, после ревью полученного каркаса.**

---

# 8. Порядок начала работы

Начать исключительно со **слайса 1 — инфраструктурный каркас**.

Не реализовывать остальные слайсы до подтверждения.

Сначала проанализировать существующие файлы uv-проекта, сохранить актуальную конфигурацию и внести минимальные необходимые изменения.

После выполнения первого слайса предоставить краткий отчёт и остановиться.
