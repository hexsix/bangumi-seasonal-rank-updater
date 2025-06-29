FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY . /app

RUN uv sync --frozen --no-cache

CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--host", "::", "--port", "8000", "--workers", "4"]
