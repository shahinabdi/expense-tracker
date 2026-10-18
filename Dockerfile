# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM builder AS test
RUN uv sync --frozen --no-install-project
COPY app ./app
COPY tests ./tests
RUN uv run --no-sync pytest -q

FROM python:3.12-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    EXPENSES_FILE=/data/expenses.json
RUN useradd --system --uid 1000 app && mkdir /data && chown app /data
COPY --chown=app app/data/expenses.json /data/expenses.json
COPY --from=builder /opt/venv /opt/venv
WORKDIR /srv
COPY --chown=app app ./app
USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
