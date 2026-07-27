# Developer onboarding

## Stack

- Python 3.13+ / FastAPI in `apps/api`
- Node 22+ / React 19 / Vite 8 in `apps/web`
- External Postgres, Redis, Keycloak, R2

## First run

1. `cp .env.example .env` and fill Undash-Cop values.
2. `cp apps/web/.env.example apps/web/.env`.
3. API:
   ```bash
   cd apps/api
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   alembic upgrade head   # applies through 0006_phase5
   uvicorn app.main:app --reload --port 8000
   ```
4. Web:
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```
5. Open http://localhost:5173 — public site works without Keycloak; `/app` requires login.

## Product flow (through Phase 5)

1. Trainers: `/app` — CRM, calendar, scheduling (recurring + availability), automations, chat (WebSocket), billing
2. Clients: `/client` after portal invite accept
3. Platform admins: `/admin`
4. Finish session now collects a 1–5 rating
5. Metrics: `GET /metrics` · K8s: `infrastructure/k8s/tetherfit.yaml`
6. `alembic upgrade head` through `0006_phase5`

## Quality commands

```bash
# API
ruff check app tests && black --check app tests && pytest

# Web
npm run typecheck && npm run lint && npm test && npm run build
```

## Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

Compose starts **api** and **web** only.
