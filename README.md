# TetherFit

AI-powered Trainer Business Operating System for solo personal trainers, freelance coaches, and small fitness studios.

> The Operating System for Modern Fitness Professionals

## Apps

| App | Path | Description |
|-----|------|-------------|
| **API** | [`apps/api`](apps/api) | FastAPI backend (Clean Architecture, multi-tenant) |
| **Web** | [`apps/web`](apps/web) | React PWA — public marketing routes + authenticated app |

## Prerequisites

External Undash-Cop services (not started by Docker Compose):

- PostgreSQL (`DATABASE_URL`)
- Redis (`REDIS_URL`)
- Keycloak (OIDC / OAuth2 + PKCE)
- Cloudflare R2 (S3-compatible object storage)

## Quick start

```bash
cp .env.example .env
# Fill in Undash-Cop Postgres, Redis, Keycloak, and R2 values

# API
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Web (separate terminal)
cd apps/web
npm install
npm run dev
```

Or with Docker Compose (**API only** for local; web is Netlify / `npm run dev`):

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Documentation

- [Architecture](docs/architecture.md)
- [Environment variables](docs/environment.md)
- [Developer onboarding](docs/onboarding.md)
- [Deployment](docs/deployment.md) (VPS API via udc-infra + Netlify web)
- [Netlify frontend](docs/netlify.md)
- [UDC deploy](docs/udc-deployment.md)

## Phase status

**Phase 6 – Production Completeness** (current): session pause/resume, calendar DnD, R2 transformation photos, SMTP email, Razorpay webhook, seed + Playwright smoke. API `0.7.0` / migration `0007_phase6`.

**Phase 5 – Polish & Growth**: recurring sessions, availability, realtime chat, push, automations, refunds/memberships, metrics, k8s.

**Phase 4 – Client Portal & Platform**: client PWA, chat, platform admin, R2 media, Celery reminders, rate limits.

**Phase 3 – Scale**: AI copilots, calendar ICS/integrations, marketplace, analytics, offline PWA, enterprise team/API keys.

**Phase 2 – Business Operations**: workouts, assessments, invoices + Razorpay/noop payments, nutrition, reports, notification abstraction.

**Phase 1 – Core Platform**: onboarding, RBAC, Client CRM, calendar + PT sessions with credits, live dashboard.

**Phase 0 – Foundation**: API/web scaffolds, Keycloak JWT, public + app shell, PWA, CI.
