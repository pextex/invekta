FROM node:22.13.0-bookworm-slim AS frontend-build
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
COPY shared/ /src/shared/
RUN npm run build

FROM python:3.12-slim-bookworm AS app
COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /uvx /bin/
ENV UV_PROJECT_ENVIRONMENT=/app/backend/.venv
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ ./
COPY shared/ /app/shared/
RUN uv sync --frozen --no-dev
COPY --from=frontend-build /src/frontend/dist /app/backend/app/static
ENV PATH="/app/backend/.venv/bin:$PATH"
EXPOSE 3000
CMD ["sh", "-c", "python -m app.run_migrations && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-3000}"]
