# Netlify frontend deploy

TetherFit web is a Vite SPA. Backend stays on UDC (`https://api.tetherfit.undash-cop.com`).

## One-time Netlify setup

1. Create a site linked to `undash-cop/tetherfit` (branch `main`).
2. Build settings are in repo-root [`netlify.toml`](../netlify.toml):
   - Base directory: `apps/web`
   - Build command: `npm run build`
   - Publish: `dist`
3. Confirm build env (already set in `netlify.toml`; override in UI if needed):

| Variable | Value |
|----------|--------|
| `VITE_API_URL` | `https://api.tetherfit.undash-cop.com` |
| `VITE_KEYCLOAK_URL` | `https://secure.undash-cop.com` |
| `VITE_KEYCLOAK_REALM` | `tetherfit` |
| `VITE_KEYCLOAK_CLIENT_ID` | `tetherfit-web` |

4. Deploy. Note the production URL (custom domain or `*.netlify.app`).

## Keycloak (required after first URL is known)

Client: `tetherfit-web` (public, PKCE S256) in realm `tetherfit`.

| Setting | Values |
|---------|--------|
| Valid redirect URIs | `https://<site>/*`, `http://localhost:5173/*` |
| Valid post logout redirect URIs | `https://<site>/*`, `http://localhost:5173/*` |
| Web origins | `https://<site>`, `http://localhost:5173` |

Login lands on `/app` after Keycloak (not `/auth/callback`).

## API CORS + JWT (UDC)

In `configs/env/apps.tetherfit.env` on the VPS, realm/issuer **must match** the SPA:

```env
UDC_JWT_ISSUER=https://secure.undash-cop.com/realms/tetherfit
KEYCLOAK_REALM=tetherfit
KEYCLOAK_CLIENT_ID=tetherfit-web
KEYCLOAK_AUDIENCE=tetherfit-api
CORS_ORIGINS=https://<your-netlify-or-custom-domain>,http://localhost:5173
```

`KEYCLOAK_SERVER_URL=http://keycloak:8080` stays in `global.env` (internal JWKS).

Then redeploy:

```bash
./scripts/deploy-apps.sh --only tetherfit
```

If the UI shows **API rejected your login token** / HTTP 401, the issuer/realm mismatch above is the usual cause.

## Local verify before deploy

```bash
cd apps/web
cp .env.example .env.local   # if needed
npm ci
npm run typecheck
npm run build
npm run preview
```

Open the preview URL and confirm login → `/app`.

## Custom domain (optional)

1. Add domain in Netlify → DNS as instructed.
2. Add the same HTTPS origin to Keycloak + `CORS_ORIGINS`.
3. Redeploy API after CORS change.
