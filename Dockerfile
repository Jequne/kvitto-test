FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=0

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY alembic.ini ./
COPY alembic ./alembic

RUN uv sync --locked --no-dev --no-editable

CMD ["uv", "run", "--no-sync", "uvicorn", "kvitto_test.main:app", "--host", "0.0.0.0", "--port", "8000"]
