## Запуск

Проект использует Python 3.11 и `uv`.

```powershell
uv sync
uv run uvicorn kvitto_test.main:app --reload
```

Swagger UI доступен по адресу `http://127.0.0.1:8000/docs`.
Для подключения к PostgreSQL задайте `DATABASE_URL` в окружении или скопируйте `.env.example` в `.env` и измените параметры подключения. База данных и таблицы этим каркасом не создаются; миграции будут добавлены в следующих слайсах.
