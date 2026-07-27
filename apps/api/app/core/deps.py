from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.permissions import PermissionContext, permission_service
from app.core.security import bearer_scheme, decode_access_token, get_current_user
from app.domain.models import User


def extract_roles(payload: dict[str, Any]) -> set[str]:
    roles: set[str] = set()
    realm = payload.get("realm_access") or {}
    if isinstance(realm, dict):
        for role in realm.get("roles") or []:
            if isinstance(role, str):
                roles.add(_normalize_role(role))
    resource = payload.get("resource_access") or {}
    if isinstance(resource, dict):
        for client_roles in resource.values():
            if isinstance(client_roles, dict):
                for role in client_roles.get("roles") or []:
                    if isinstance(role, str):
                        roles.add(_normalize_role(role))
    return roles


def _normalize_role(role: str) -> str:
    mapping = {
        "owner": "business_owner",
        "admin": "platform_admin",
        "business-owner": "business_owner",
        "platform-admin": "platform_admin",
    }
    return mapping.get(role, role)


@dataclass
class AuthPrincipal:
    user: User
    roles: set[str] = field(default_factory=set)
    payload: dict[str, Any] = field(default_factory=dict)

    def permission_context(self) -> PermissionContext:
        roles = set(self.roles)
        if self.user.org_role:
            roles.add(self.user.org_role)
        if not roles and self.user.organization_id and self.user.onboarding_completed:
            roles.add("business_owner")
        return PermissionContext(user=self.user, roles=roles)

    def is_client(self) -> bool:
        ctx = self.permission_context()
        return (
            "client" in ctx.roles
            and "business_owner" not in ctx.roles
            and "trainer" not in ctx.roles
        )

    def is_platform_admin(self) -> bool:
        return "platform_admin" in self.permission_context().roles


async def get_auth_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_user),
) -> AuthPrincipal:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials, settings)
    return AuthPrincipal(user=user, roles=extract_roles(payload), payload=payload)


def require_permission(permission: str):
    async def _dep(principal: AuthPrincipal = Depends(get_auth_principal)) -> AuthPrincipal:
        if not permission_service.can(principal.permission_context(), permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return principal

    return _dep


def require_organization(principal: AuthPrincipal = Depends(get_auth_principal)) -> AuthPrincipal:
    if principal.is_platform_admin() and principal.user.organization_id is None:
        return principal
    if principal.user.organization_id is None or not principal.user.onboarding_completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization onboarding required",
            headers={"X-TetherFit-Onboarding": "required"},
        )
    return principal


def org_id(principal: AuthPrincipal) -> UUID:
    if principal.user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization onboarding required",
        )
    return principal.user.organization_id


def require_platform_admin(
    principal: AuthPrincipal = Depends(require_permission("platform:admin")),
) -> AuthPrincipal:
    if not principal.is_platform_admin():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform admin required")
    return principal
