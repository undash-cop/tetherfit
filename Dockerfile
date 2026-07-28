# syntax=docker/dockerfile:1
# UDC contract: repo-root Dockerfile, API on :8000.

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/pyproject.toml apps/api/README.md ./
COPY apps/api/app ./app
COPY apps/api/alembic ./alembic
COPY apps/api/alembic.ini ./

RUN pip install --upgrade pip && pip install -e .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
