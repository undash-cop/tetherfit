# TetherFit Web

React 19 + Vite PWA. Production host: **Netlify** (see [`docs/netlify.md`](../../docs/netlify.md)).

```bash
cp .env.example .env.local
npm install
npm run dev
```

## Production build (same as Netlify)

```bash
npm ci
npm run typecheck
npm run build
npm run preview
```

## Routes

| Path | Access |
|------|--------|
| `/`, `/features`, `/pricing`, `/contact`, `/marketplace` | Public |
| `/login` | Starts Keycloak (redirects to `/app`) |
| `/app/*`, `/client/*`, `/admin/*` | Authenticated (Keycloak) |

## Playwright smoke

```bash
npm run build
# API should be on :8000 for /health
npm run test:e2e
```

CI runs public routes (`/`, `/features`, `/marketplace`) plus API `/health` — no Keycloak.
