#!/bin/sh
# UDC-style entrypoint (same pattern as hiring-journey): wait for DB, migrate, then exec CMD.
set -eu

echo "==> Waiting for database (up to 60s)..."
ready=0
i=1
while [ "$i" -le 30 ]; do
  if python -c "
from sqlalchemy import create_engine, text
from app.core.config import get_settings

url = get_settings().database_url
for a, b in (
    ('postgresql+asyncpg://', 'postgresql+psycopg://'),
    ('postgresql+psycopg2://', 'postgresql+psycopg://'),
):
    if url.startswith(a):
        url = b + url[len(a):]
        break
engine = create_engine(url, pool_pre_ping=True)
with engine.connect() as conn:
    conn.execute(text('SELECT 1'))
print('db ok:', url.split('@')[-1] if '@' in url else url)
"; then
    ready=1
    break
  fi
  echo "    attempt $i/30 — database not reachable yet"
  sleep 2
  i=$((i + 1))
done

if [ "$ready" -ne 1 ]; then
  echo "ERROR: database unreachable — check DATABASE_URL (postgresql+asyncpg://…@postgres:5432/tetherfit)." >&2
  exit 1
fi

# Run migrations only for the API process (not Celery worker/beat) to avoid race.
if [ "${1:-}" = "uvicorn" ]; then
  echo "==> Running migrations"
  if ! alembic upgrade head; then
    echo "ERROR: alembic upgrade failed — see traceback above." >&2
    exit 1
  fi
  echo "==> Starting API"
fi

exec "$@"
