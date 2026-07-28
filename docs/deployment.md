# Deployment

## Target topology

| Surface | Where | How |
|---------|--------|-----|
| **API** | UDC VPS (`udc-infra`) | Docker → nginx TLS → `https://api.tetherfit.undash-cop.com` |
| **Web** | **Netlify** | Vite static build (`netlify.toml`) |

Do **not** deploy the web Docker image to the VPS. Local `docker/docker-compose.yml` starts API + worker + beat.

## UDC (VPS) — API

Follow the [udc-infra](https://github.com/undash-cop/udc-infra) app Docker contract (`docs/app-docker-contract.md` in that repo):

1. Repo-root **`Dockerfile`** builds the API from `apps/api`.
2. Registered as service **`tetherfit`** in `udc-infra/configs/deploy/apps.json`.
3. Env template: `udc-infra/configs/env/templates/apps.tetherfit.env.example` → `apps.tetherfit.env`.
4. Create DB `tetherfit` (init script `postgres/init/04-tetherfit-db.sh`, or `CREATE DATABASE` once).
5. DNS + TLS for `api.tetherfit.undash-cop.com`, then:

```bash
cd /opt/udc/udc-infra
./scripts/init-env.sh   # if apps.tetherfit.env missing
# Edit configs/env/apps.tetherfit.env
./scripts/issue-tls-certs-data.sh
./scripts/deploy-apps.sh --only tetherfit
docker compose -f docker/docker-compose.apps.phase.yml up -d tetherfit-worker tetherfit-beat
```

Verify:

```bash
docker exec udc-tetherfit curl -fsS http://127.0.0.1:8000/health
curl -fsS https://api.tetherfit.undash-cop.com/health
```

### Critical UDC env

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://…@postgres:5432/tetherfit` |
| `KEYCLOAK_SERVER_URL` | Internal `http://keycloak:8080` (from `global.env`) |
| `UDC_JWT_ISSUER` | Public `https://secure.undash-cop.com/realms/<realm>` |
| `CORS_ORIGINS` | Netlify production (+ preview) origins |
| `REDIS_URL` | Redis on `udc-network` |

## Netlify — frontend

- Config: root [`netlify.toml`](../netlify.toml) (`base = apps/web`).
- Build env: `VITE_API_URL`, `VITE_KEYCLOAK_*`.
- Keycloak: add Netlify origin + `/auth/callback` redirect URIs.

## Local development

```bash
# API + worker + beat (repo root)
docker compose -f docker/docker-compose.yml up --build
# or uvicorn from apps/api

# Web
cd apps/web && npm run dev
```

## Migrations

The API container entrypoint runs `alembic upgrade head` automatically on every start (before uvicorn). Worker/beat skip migrate to avoid races.

Manual one-shot if needed:

```bash
docker compose -f docker/docker-compose.apps.phase.yml run --rm tetherfit alembic upgrade head
```

## Health / metrics

- `GET /health` — DB required for `"status":"ok"`
- `GET /metrics` — Prometheus (scraped when `metrics_scrape: true`)

## Legacy

`infrastructure/k8s/` is reference-only; production path is **udc-infra Compose on the VPS**, not Kubernetes.
