FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /srv
ENV UV_COMPILE_BYTECODE=1 PATH="/srv/.venv/bin:$PATH"
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN uv sync --frozen --no-dev
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
