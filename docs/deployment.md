# Deployment

## Containers

- `apps/api/Dockerfile` — Uvicorn on port 8000
- `apps/web/Dockerfile` — multi-stage Vite build + Nginx

Orchestrate with `docker/docker-compose.yml` for simple environments, or Kubernetes with Traefik ingress (labels commented in Compose).

## Suggested hosts

| Host | Service |
|------|---------|
| `app.tetherfit…` or apex | `apps/web` |
| `api.tetherfit…` | `apps/api` |

## Runtime config

Inject secrets via environment / secret store — never bake Keycloak, DB, Redis, or R2 credentials into images.

## Migrations

Run `alembic upgrade head` as a release job before rolling new API pods.

## Health

`GET /health` reports database (required), Redis, and R2 status.

Responses include `X-Request-ID` and `X-Response-Time-ms`. API rate limit defaults to 180 requests/minute/IP.

## Workers

```bash
cd apps/api
celery -A app.infrastructure.celery_app.celery_app worker -B -l info
```

Beat schedule runs `tetherfit.session_reminders` hourly (notify sessions starting within 2 hours).

## Kubernetes readiness

Manifests live in [`infrastructure/k8s/tetherfit.yaml`](../infrastructure/k8s/tetherfit.yaml):

- `tetherfit-api` Deployment (migrate initContainer + readiness/liveness)
- `tetherfit-web` Deployment
- `tetherfit-worker` Celery worker+beat
- Services for api/web

Create a `tetherfit-secrets` Secret with Undash-Cop env vars before apply.

Prometheus scrape `GET /metrics` on the API service.
