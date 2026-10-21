FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /srv
ENV UV_COMPILE_BYTECODE=1 PATH="/srv/.venv/bin:$PATH"
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN uv sync --frozen --no-dev
RUN useradd --system --no-create-home --uid 10001 app
USER app
EXPOSE 8000
# python is in the image, curl is not
HEALTHCHECK --interval=5s --timeout=5s --start-period=20s --retries=10 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"]
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
