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
