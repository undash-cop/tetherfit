# Environment variables

Copy [`.env.example`](../.env.example) to `.env` at the repo root. Also copy [`apps/web/.env.example`](../apps/web/.env.example) for Vite.

## Required external services

| Variable | Service |
|----------|---------|
| `DATABASE_URL` | Undash-Cop PostgreSQL (`postgresql+asyncpg://…/tetherfit`) |
| `REDIS_URL` | Undash-Cop Redis |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis DBs for Celery |
| `KEYCLOAK_SERVER_URL` / `KEYCLOAK_REALM` | Undash-Cop Keycloak |
| `KEYCLOAK_CLIENT_ID` / `KEYCLOAK_AUDIENCE` | Public web client + API audience |
| `VITE_KEYCLOAK_*` | Same realm/client for the SPA |
| `R2_*` | Cloudflare R2 S3 credentials |

## Keycloak client checklist

1. Create public client `tetherfit-web` with PKCE (S256).
2. Valid redirect URIs: `http://localhost:5173/*`, production app origins.
3. Web origins: matching SPA origins.
4. Optional confidential API client / audience mapper for `tetherfit-api`.

## Database

Prefer a dedicated database named `tetherfit`. Run migrations from `apps/api`:

```bash
alembic upgrade head
```
