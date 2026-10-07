# syntax=docker/dockerfile:1
# UDC contract: repo-root Dockerfile, API on :8000.
# Alpine — cuts Debian slim CVE noise. Entrypoint waits for Postgres + alembic.

FROM python:3.14.8-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apk add --no-cache \
    build-base \
    postgresql-dev \
    libffi-dev \
    linux-headers

WORKDIR /build
COPY apps/api/pyproject.toml apps/api/README.md ./
COPY apps/api/app ./app
COPY apps/api/alembic ./alembic
COPY apps/api/alembic.ini ./

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# psycopg[binary] has no musl wheels — build psycopg[c] against libpq.
RUN pip install --upgrade pip setuptools wheel \
    && sed -i 's/psycopg\[binary\]/psycopg[c]/g' pyproject.toml \
    && pip install --no-cache-dir . \
    && python -c "import psycopg; from psycopg import pq; assert pq.__impl__ == 'c', pq.__impl__"

FROM python:3.14.8-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH"

RUN apk add --no-cache \
    bash \
    ca-certificates \
    curl \
    libpq \
    libffi

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /build/app ./app
COPY --from=builder /build/alembic ./alembic
COPY --from=builder /build/alembic.ini ./
COPY --from=builder /build/pyproject.toml ./
COPY docker/api-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
