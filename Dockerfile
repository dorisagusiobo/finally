# syntax=docker/dockerfile:1

# ---- Stage 1: build the frontend static export ----
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python backend + static frontend ----
FROM python:3.12-slim AS backend

# uv provides a fast, reproducible install from the lockfile.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app/backend

COPY backend/pyproject.toml backend/uv.lock backend/README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/app ./app
RUN uv sync --frozen --no-dev

# main.py serves static files from app/static if present.
COPY --from=frontend-build /app/frontend/out ./app/static

WORKDIR /app
EXPOSE 8000

# Single worker: the in-memory PriceCache and market-data background task
# assume one process, and SQLite doesn't handle concurrent writers well
# (PLAN.md §13 #9).
CMD ["/app/backend/.venv/bin/uvicorn", "app.main:app", "--app-dir", "/app/backend", "--host", "0.0.0.0", "--port", "8000"]
