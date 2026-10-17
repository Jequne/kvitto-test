## Локальный запуск

Проект использует Python 3.11 и `uv`. Для локального запуска сначала установите
`uv` (команда для Windows PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

После установки откройте новый терминал и проверьте команду `uv --version`.
Другие способы установки приведены в
[официальной документации uv](https://docs.astral.sh/uv/getting-started/installation/).
Затем из корня проекта выполните:

```powershell
uv sync
uv run uvicorn kvitto_test.main:app --reload
```

Swagger UI доступен по адресу `http://127.0.0.1:8000/docs`.
Для подключения к PostgreSQL задайте `DATABASE_URL` в окружении или скопируйте `.env.example` в `.env` и измените параметры подключения.

## Запуск в Docker Compose

Для этого способа локальная установка `uv` не требуется: он включён в образ API.

```powershell
docker compose up --build -d
docker compose exec api uv run --no-sync alembic upgrade head
```

API доступен по адресу `http://127.0.0.1:8000/docs`. PostgreSQL доступен на
`127.0.0.1:5432` с параметрами из `.env.example`. Если этот порт уже занят,
задайте `POSTGRES_PORT` перед запуском Compose. Внутри контейнера API
подключается к сервису `db`; локальный запуск Python использует прежнюю
настройку `DATABASE_URL`.

## Примеры запросов

После запуска API и применения миграций выполните в PowerShell:

```powershell
curl.exe http://127.0.0.1:8000/tariffs
```

Создание платежа по тарифу `Basic` из начальных данных миграции:

```powershell
'{"tariff_id":"a1138f45-bb1d-4cc3-90e5-4d84ec6b50c1","email":"buyer@example.com","method":"card"}' |
    curl.exe -X POST http://127.0.0.1:8000/payments -H "Content-Type: application/json" --data-binary "@-"
```

## Запуск тестов

Из корня проекта установите зависимости и запустите все тесты:

```powershell
uv sync
uv run pytest
```

Текущие тесты используют подставной репозиторий, поэтому PostgreSQL для их
запуска не требуется.
