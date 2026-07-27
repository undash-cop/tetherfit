# TetherFit API

FastAPI backend for TetherFit. Clean Architecture, multi-tenant, Keycloak JWT auth.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

OpenAPI: http://localhost:8000/docs
