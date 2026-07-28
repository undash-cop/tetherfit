# Developer onboarding

## Stack

- Python 3.13+ / FastAPI in `apps/api`
- Node 22+ / React 19 / Vite 8 in `apps/web`
- External Postgres, Redis, Keycloak, R2

## First run

1. `cp .env.example .env` and fill Undash-Cop values (optional `SMTP_*` for real email).
2. `cp apps/web/.env.example apps/web/.env`.
3. API:
   ```bash
   cd apps/api
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   alembic upgrade head   # through 0007_phase6
   uvicorn app.main:app --reload --port 8000
   ```
4. Optional demo data:
   ```bash
   PYTHONPATH=apps/api python scripts/seed_demo.py
   ```
5. Web:
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```
6. Open http://localhost:5173 — public site works without Keycloak; `/app` requires login.

## Product flow (through Phase 6)

1. Trainers: `/app` — CRM, calendar (drag-drop), pause/resume sessions, assessments with photos, billing, chat
2. Clients: `/client` progress photos after portal invite
3. Platform admins: `/admin`
4. Payments: Razorpay confirm path + public webhook settle
5. Notifications: SMTP when configured, else noop
6. `alembic upgrade head` through `0007_phase6`

## Quality commands

```bash
# API
ruff check app tests && black --check app tests && pytest

# Web
npm run typecheck && npm run lint && npm test && npm run build

# Playwright smoke (public + API health; no Keycloak)
cd apps/web && npm run build && npm run test:e2e
```

Authenticated calendar e2e is local-only: log in, then exercise day/week drag-drop on `/app/calendar`.

## Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

Compose starts **api + worker + beat**. Frontend: `npm run dev` or Netlify.
