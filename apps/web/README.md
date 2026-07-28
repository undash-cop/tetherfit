# TetherFit Web

React 19 + Vite PWA with public marketing routes and authenticated `/app` shell.

```bash
cp .env.example .env
npm install
npm run dev
```

## Routes

| Path | Access |
|------|--------|
| `/`, `/features`, `/pricing`, `/contact` | Public |
| `/login`, `/auth/callback` | Auth |
| `/app/*` | Authenticated (Keycloak) |

## Playwright smoke

```bash
npm run build
# API should be on :8000 for /health
npm run test:e2e
```

CI runs public routes (`/`, `/features`, `/marketplace`) plus API `/health` — no Keycloak.

**Local authenticated calendar:** seed with `python scripts/seed_demo.py`, sign in, open `/app/calendar`, drag session chips on day/week views.
