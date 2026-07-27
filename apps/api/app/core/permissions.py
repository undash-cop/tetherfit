"""Permission service — never check roles directly; always use can()."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.models import User

PERMISSION_CATALOG: frozenset[str] = frozenset(
    {
        "client:create",
        "client:view",
        "client:update",
        "client:delete",
        "session:create",
        "session:start",
        "session:finish",
        "session:cancel",
        "workout:create",
        "workout:assign",
        "workout:update",
        "invoice:create",
        "invoice:view",
        "invoice:update",
        "payment:view",
        "payment:collect",
        "reports:view",
        "settings:update",
        "ai:use",
        "marketplace:manage",
        "integrations:manage",
        "team:manage",
        "analytics:view",
        "chat:use",
        "portal:access",
        "media:upload",
        "platform:admin",
    }
)

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "platform_admin": PERMISSION_CATALOG,
    "business_owner": PERMISSION_CATALOG - frozenset({"platform:admin"}),
    "trainer": frozenset(
        {
            "client:create",
            "client:view",
            "client:update",
            "session:create",
            "session:start",
            "session:finish",
            "session:cancel",
            "workout:create",
            "workout:assign",
            "workout:update",
            "invoice:view",
            "payment:view",
            "payment:collect",
            "reports:view",
            "ai:use",
            "analytics:view",
            "integrations:manage",
            "chat:use",
            "media:upload",
        }
    ),
    "client": frozenset(
        {
            "portal:access",
            "client:view",
            "session:create",
            "invoice:view",
            "payment:view",
            "chat:use",
            "media:upload",
        }
    ),
}


@dataclass
class PermissionContext:
    user: User
    roles: set[str] = field(default_factory=set)
    extra_permissions: set[str] = field(default_factory=set)

    def resolved_permissions(self) -> set[str]:
        perms: set[str] = set(self.extra_permissions)
        for role in self.roles:
            perms |= set(ROLE_PERMISSIONS.get(role, frozenset()))
        if not perms:
            perms |= {
                "client:view",
                "session:create",
                "reports:view",
                "workout:create",
                "workout:assign",
                "workout:update",
                "invoice:view",
                "payment:view",
                "ai:use",
                "analytics:view",
                "marketplace:manage",
                "integrations:manage",
                "team:manage",
                "settings:update",
                "chat:use",
                "media:upload",
            }
        return perms


class PermissionService:
    def can(self, ctx: PermissionContext | User, permission: str) -> bool:
        if isinstance(ctx, User):
            ctx = PermissionContext(user=ctx)
        return permission in ctx.resolved_permissions()

    def require(self, ctx: PermissionContext | User, permission: str) -> None:
        if not self.can(ctx, permission):
            raise PermissionError(f"Missing permission: {permission}")


permission_service = PermissionService()
