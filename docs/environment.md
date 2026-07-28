# Environment variables

Copy [`.env.example`](../.env.example) to `.env` at the repo root. Also copy [`apps/web/.env.example`](../apps/web/.env.example) for Vite.

## Required external services

| Variable | Service |
|----------|---------|
| `DATABASE_URL` | Undash-Cop / UDC PostgreSQL (`postgresql+asyncpg://…/tetherfit`) |
| `REDIS_URL` | Undash-Cop Redis |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis DBs for Celery |
| `KEYCLOAK_SERVER_URL` / `KEYCLOAK_REALM` | Internal Keycloak on UDC: `http://keycloak:8080` |
| `UDC_JWT_ISSUER` | Public JWT `iss` (e.g. `https://secure.undash-cop.com/realms/undash`) |
| `KEYCLOAK_CLIENT_ID` / `KEYCLOAK_AUDIENCE` | Public web client + API audience |
| `VITE_KEYCLOAK_*` / `VITE_API_URL` | Netlify / local SPA (build-time) |
| `CORS_ORIGINS` | Must include Netlify origin(s) in production |

## Optional

| Variable | Notes |
|----------|--------|
| `R2_*` | Cloudflare R2 media |
| `SMTP_*` | Email (noop if `SMTP_HOST` unset) |
| `RAZORPAY_*` | Payments + webhook secret |
| `VAPID_*` | Web push |
| `AI_*` | Copilots |

## Keycloak client checklist

1. Create public client `tetherfit-web` with PKCE (S256).
2. Valid redirect URIs: `http://localhost:5173/*`, Netlify app origins + `/auth/callback`.
3. Web origins: matching SPA origins.
4. Optional confidential API client / audience mapper for `tetherfit-api`.

## Database

Prefer a dedicated database named `tetherfit`. On UDC, migrations run in the API container entrypoint. Locally:

```bash
cd apps/api && alembic upgrade head
```
