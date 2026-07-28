#!/bin/sh
set -eu

MODE="${1:-api}"

wait_for_db() {
  echo "==> Waiting for database (up to 60s)..."
  ready=0
  i=1
  while [ "$i" -le 30 ]; do
    if python -c "
from sqlalchemy import create_engine, text
from app.core.config import get_settings

url = get_settings().database_url
# Celery/alembic need a sync driver
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
print('db ok')
"; then
      ready=1
      break
    fi
    echo "    attempt $i/30 — database not reachable yet"
    sleep 2
    i=$((i + 1))
  done

  if [ "$ready" -ne 1 ]; then
    echo "ERROR: database unreachable — check DATABASE_URL (use postgresql+asyncpg://…)." >&2
    exit 1
  fi
}

run_migrations() {
  echo "==> Running migrations"
  if ! alembic upgrade head; then
    echo "ERROR: alembic upgrade failed — see traceback above." >&2
    exit 1
  fi
}

case "$MODE" in
  api)
    wait_for_db
    run_migrations
    echo "==> Starting API"
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
    ;;
  worker)
    wait_for_db
    echo "==> Starting Celery worker + beat"
    exec celery -A app.infrastructure.celery_app.celery_app worker -B -l info
    ;;
  *)
    # Allow override: docker run … uvicorn …
    exec "$@"
    ;;
esac
