# UDC platform deployment (TetherFit API)

TetherFit API on the shared **UDC** stack (`udc-infra`, `deploy-apps.sh`). Frontend stays on **Netlify**.

| Item | Value |
|------|--------|
| Service | `tetherfit` |
| Container | `udc-tetherfit` |
| Host | `https://api.tetherfit.undash-cop.com` |
| Clone path | `/opt/udc/repos/tetherfit` |
| Deploy | `./scripts/deploy-apps.sh --only tetherfit` |
| Migrations | Automatic in API entrypoint (`alembic upgrade head`) |
| Worker/Beat | `docker compose -f docker/docker-compose.apps.phase.yml up -d tetherfit-worker tetherfit-beat` |

## First-time checklist

1. Push this monorepo to `git@github.com:undash-cop/tetherfit.git` (or update `git_url` in `apps.json`).
2. On VPS: ensure `tetherfit` DB exists (`04-tetherfit-db.sh` only runs on fresh Postgres volume — otherwise `CREATE DATABASE tetherfit`).
3. `./scripts/init-env.sh` → fill `configs/env/apps.tetherfit.env`.
4. DNS A/AAAA for `api.tetherfit.undash-cop.com` → VPS; issue TLS; deploy.
5. Point Netlify `VITE_API_URL` at the public API host; set `CORS_ORIGINS` accordingly.

## Health failed after deploy

```bash
docker logs udc-tetherfit --tail 120
docker exec udc-tetherfit curl -fsS http://127.0.0.1:8000/health
# JWKS via internal Keycloak:
docker exec udc-tetherfit curl -fsS http://keycloak:8080/realms/undash/protocol/openid-connect/certs | head
```

Common causes: wrong `DATABASE_URL`, missing `UDC_JWT_ISSUER` vs public token `iss`, CORS blocking Netlify.

## Related

- [deployment.md](./deployment.md)
- udc-infra `docs/app-docker-contract.md`
