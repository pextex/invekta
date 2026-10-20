# syntax=docker/dockerfile:1
FROM node:22.13.0-bookworm-slim AS frontend-build
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca; fi; \
    npm ci
COPY frontend/ ./
COPY shared/ /src/shared/
RUN npm run build:hosting

FROM python:3.12-slim-bookworm AS app
COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /uvx /bin/
ENV UV_PROJECT_ENVIRONMENT=/app/backend/.venv
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export SSL_CERT_FILE=/run/secrets/proxy_ca; fi; \
    uv sync --frozen --no-dev --no-install-project
COPY backend/ ./
COPY shared/ /app/shared/
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export SSL_CERT_FILE=/run/secrets/proxy_ca; fi; \
    uv sync --frozen --no-dev
COPY --from=frontend-build /src/frontend/dist /app/backend/app/static
RUN groupadd --system crm && useradd --system --uid 10001 --gid crm crm \
    && chmod -R a+rX /app/backend /app/shared
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/backend/.venv/bin:$PATH"
USER crm
EXPOSE 3000
CMD ["sh", "-c", "python -m app.run_migrations && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-3000}"]
