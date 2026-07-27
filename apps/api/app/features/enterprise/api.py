from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.domain.models import Organization, OrgApiKey, TeamInvite, User

router = APIRouter(prefix="/api/v1/enterprise", tags=["enterprise"])


class MemberOut(BaseModel):
    id: UUID
    email: str | None
    full_name: str
    org_role: str
    last_active_at: datetime | None

    model_config = {"from_attributes": True}


class InviteIn(BaseModel):
    email: EmailStr
    org_role: str = Field(default="trainer", pattern="^(trainer|business_owner|manager)$")


class InviteOut(BaseModel):
    id: UUID
    email: str
    org_role: str
    status: str
    token: str
    expires_at: datetime

    model_config = {"from_attributes": True}


class BrandingIn(BaseModel):
    branding_json: str | None = None
    gstin: str | None = None
    plan: str | None = None
    working_hours: dict | None = None
    feature_flags: dict | None = None
    timezone: str | None = None


class OrgEnterpriseOut(BaseModel):
    id: UUID
    name: str
    slug: str
    timezone: str
    branding_json: str | None
    gstin: str | None
    plan: str
    subscription_status: str
    working_hours: dict
    feature_flags: dict

    model_config = {"from_attributes": True}


class ApiKeyCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class ApiKeyCreatedOut(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    api_key: str


class ApiKeyOut(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    last_used_at: datetime | None
    revoked_at: datetime | None

    model_config = {"from_attributes": True}


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


@router.get("/org", response_model=OrgEnterpriseOut)
async def get_org_enterprise(
    principal: AuthPrincipal = Depends(require_permission("settings:update")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    org = await db.get(Organization, org_id(principal))
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.patch("/org", response_model=OrgEnterpriseOut)
async def patch_org_enterprise(
    body: BrandingIn,
    principal: AuthPrincipal = Depends(require_permission("settings:update")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    org = await db.get(Organization, org_id(principal))
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(org, k, v)
    org.updated_by = principal.user.id
    await db.commit()
    await db.refresh(org)
    return org


@router.get("/team", response_model=list[MemberOut])
async def list_team(
    principal: AuthPrincipal = Depends(require_permission("team:manage")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    oid = org_id(principal)
    rows = await db.scalars(
        select(User).where(User.organization_id == oid, User.deleted_at.is_(None))
    )
    return list(rows)


@router.post("/team/invites", response_model=InviteOut, status_code=status.HTTP_201_CREATED)
async def create_invite(
    body: InviteIn,
    principal: AuthPrincipal = Depends(require_permission("team:manage")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> TeamInvite:
    invite = TeamInvite(
        organization_id=org_id(principal),
        email=str(body.email).lower(),
        org_role=body.org_role,
        token=token_urlsafe(24),
        status="pending",
        expires_at=datetime.now(UTC) + timedelta(days=14),
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite


@router.get("/team/invites", response_model=list[InviteOut])
async def list_invites(
    principal: AuthPrincipal = Depends(require_permission("team:manage")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[TeamInvite]:
    oid = org_id(principal)
    rows = await db.scalars(
        select(TeamInvite).where(
            TeamInvite.organization_id == oid,
            TeamInvite.deleted_at.is_(None),
            TeamInvite.status == "pending",
        )
    )
    return list(rows)


@router.post("/team/invites/{token}/accept", response_model=MemberOut)
async def accept_invite(
    token: str,
    principal: AuthPrincipal = Depends(require_permission("settings:update")),
    db: AsyncSession = Depends(get_db),
) -> User:
    invite = await db.scalar(
        select(TeamInvite).where(
            TeamInvite.token == token,
            TeamInvite.status == "pending",
            TeamInvite.deleted_at.is_(None),
        )
    )
    if not invite or invite.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Invite invalid or expired")
    user = principal.user
    user.organization_id = invite.organization_id
    user.org_role = invite.org_role
    user.onboarding_completed = True
    invite.status = "accepted"
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/api-keys", response_model=list[ApiKeyOut])
async def list_api_keys(
    principal: AuthPrincipal = Depends(require_permission("settings:update")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[OrgApiKey]:
    oid = org_id(principal)
    rows = await db.scalars(
        select(OrgApiKey).where(
            OrgApiKey.organization_id == oid,
            OrgApiKey.deleted_at.is_(None),
        )
    )
    return list(rows)


@router.post("/api-keys", response_model=ApiKeyCreatedOut, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: ApiKeyCreateIn,
    principal: AuthPrincipal = Depends(require_permission("settings:update")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreatedOut:
    raw = f"tf_{token_urlsafe(32)}"
    prefix = raw[:10]
    row = OrgApiKey(
        organization_id=org_id(principal),
        name=body.name,
        key_prefix=prefix,
        key_hash=_hash_key(raw),
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ApiKeyCreatedOut(id=row.id, name=row.name, key_prefix=prefix, api_key=raw)


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("settings:update")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> None:
    oid = org_id(principal)
    row = await db.scalar(
        select(OrgApiKey).where(
            OrgApiKey.id == key_id,
            OrgApiKey.organization_id == oid,
            OrgApiKey.deleted_at.is_(None),
        )
    )
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    row.revoked_at = datetime.now(UTC)
    row.deleted_at = datetime.now(UTC)
    await db.commit()
