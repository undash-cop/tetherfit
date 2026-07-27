from __future__ import annotations

from typing import Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.domain.models import User

bearer_scheme = HTTPBearer(auto_error=False)

_jwks_clients: dict[str, PyJWKClient] = {}


def _get_jwks_client(settings: Settings) -> PyJWKClient:
    url = settings.keycloak_jwks_url
    if url not in _jwks_clients:
        _jwks_clients[url] = PyJWKClient(url, cache_keys=True, lifespan=3600)
    return _jwks_clients[url]


def decode_access_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    try:
        signing_key = _get_jwks_client(settings).get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            issuer=settings.keycloak_issuer,
            options={"verify_aud": False},
        )
        azp = payload.get("azp") or payload.get("client_id")
        aud = payload.get("aud")
        allowed = {settings.keycloak_client_id, settings.keycloak_audience}
        audience_ok = False
        if isinstance(aud, str):
            audience_ok = aud in allowed
        elif isinstance(aud, list):
            audience_ok = any(a in allowed for a in aud)
        if azp and azp in allowed:
            audience_ok = True
        if settings.keycloak_audience and not audience_ok and azp != settings.keycloak_client_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token audience mismatch",
            )
        return payload
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials, settings)
    keycloak_user_id = payload.get("sub")
    if not keycloak_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing sub")

    result = await db.execute(select(User).where(User.keycloak_user_id == keycloak_user_id))
    user = result.scalar_one_or_none()

    if user is None:
        email = payload.get("email")
        name = payload.get("name") or payload.get("preferred_username") or ""
        user = User(
            keycloak_user_id=keycloak_user_id,
            email=email,
            full_name=name,
            timezone=payload.get("zoneinfo") or "UTC",
        )
        db.add(user)
        await db.flush()

    user.touch_active()
    await db.flush()
    return user


async def probe_jwks(settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(settings.keycloak_jwks_url)
            return response.status_code == 200 and "keys" in response.json()
    except Exception:
        return False
