from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, require_platform_admin
from app.domain.models import (
    Client,
    Organization,
    PlatformFlag,
    PtSession,
    SupportTicket,
    User,
)

router = APIRouter(prefix="/api/v1/admin", tags=["platform-admin"])


class OrgAdminOut(BaseModel):
    id: UUID
    name: str
    slug: str
    plan: str
    subscription_status: str
    created_at: datetime
    users_count: int = 0
    clients_count: int = 0

    model_config = {"from_attributes": True}


class UsageOut(BaseModel):
    organizations: int
    users: int
    clients: int
    sessions_30d: int
    generated_at: datetime


class FlagIn(BaseModel):
    key: str = Field(min_length=2, max_length=120)
    enabled: bool = False
    description: str | None = None
    payload: dict = Field(default_factory=dict)


class FlagOut(BaseModel):
    id: UUID
    key: str
    enabled: bool
    description: str | None
    payload: dict

    model_config = {"from_attributes": True}


class TicketIn(BaseModel):
    subject: str = Field(min_length=3, max_length=255)
    body: str = Field(min_length=3)
    organization_id: UUID | None = None
    priority: str = "normal"


class TicketOut(BaseModel):
    id: UUID
    subject: str
    body: str
    status: str
    priority: str
    organization_id: UUID | None

    model_config = {"from_attributes": True}


class SubscriptionPatch(BaseModel):
    plan: str | None = None
    subscription_status: str | None = None
    feature_flags: dict | None = None


@router.get("/usage", response_model=UsageOut)
async def platform_usage(
    _: AuthPrincipal = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> UsageOut:
    orgs = await db.scalar(
        select(func.count()).select_from(Organization).where(Organization.deleted_at.is_(None))
    )
    users = await db.scalar(select(func.count()).select_from(User).where(User.deleted_at.is_(None)))
    clients = await db.scalar(
        select(func.count()).select_from(Client).where(Client.deleted_at.is_(None))
    )
    from datetime import timedelta

    start = datetime.now(UTC) - timedelta(days=30)
    sessions = await db.scalar(
        select(func.count())
        .select_from(PtSession)
        .where(PtSession.deleted_at.is_(None), PtSession.starts_at >= start)
    )
    return UsageOut(
        organizations=int(orgs or 0),
        users=int(users or 0),
        clients=int(clients or 0),
        sessions_30d=int(sessions or 0),
        generated_at=datetime.now(UTC),
    )


@router.get("/organizations", response_model=list[OrgAdminOut])
async def list_organizations(
    _: AuthPrincipal = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[OrgAdminOut]:
    orgs = list(
        await db.scalars(
            select(Organization)
            .where(Organization.deleted_at.is_(None))
            .order_by(Organization.created_at.desc())
            .limit(100)
        )
    )
    out: list[OrgAdminOut] = []
    for org in orgs:
        users_count = await db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.organization_id == org.id, User.deleted_at.is_(None))
        )
        clients_count = await db.scalar(
            select(func.count())
            .select_from(Client)
            .where(Client.organization_id == org.id, Client.deleted_at.is_(None))
        )
        out.append(
            OrgAdminOut(
                id=org.id,
                name=org.name,
                slug=org.slug,
                plan=org.plan,
                subscription_status=org.subscription_status,
                created_at=org.created_at,
                users_count=int(users_count or 0),
                clients_count=int(clients_count or 0),
            )
        )
    return out


@router.patch("/organizations/{organization_id}", response_model=OrgAdminOut)
async def patch_organization(
    organization_id: UUID,
    body: SubscriptionPatch,
    _: AuthPrincipal = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> OrgAdminOut:
    org = await db.get(Organization, organization_id)
    if not org or org.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Organization not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(org, k, v)
    await db.commit()
    await db.refresh(org)
    return OrgAdminOut(
        id=org.id,
        name=org.name,
        slug=org.slug,
        plan=org.plan,
        subscription_status=org.subscription_status,
        created_at=org.created_at,
    )


@router.get("/flags", response_model=list[FlagOut])
async def list_flags(
    _: AuthPrincipal = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[PlatformFlag]:
    rows = await db.scalars(
        select(PlatformFlag).where(PlatformFlag.deleted_at.is_(None)).order_by(PlatformFlag.key)
    )
    return list(rows)


@router.put("/flags", response_model=FlagOut)
async def upsert_flag(
    body: FlagIn,
    principal: AuthPrincipal = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> PlatformFlag:
    row = await db.scalar(
        select(PlatformFlag).where(PlatformFlag.key == body.key, PlatformFlag.deleted_at.is_(None))
    )
    if row:
        row.enabled = body.enabled
        row.description = body.description
        row.payload = body.payload
        row.updated_by = principal.user.id
    else:
        row = PlatformFlag(
            key=body.key,
            enabled=body.enabled,
            description=body.description,
            payload=body.payload,
            created_by=principal.user.id,
            updated_by=principal.user.id,
        )
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/tickets", response_model=list[TicketOut])
async def list_tickets(
    _: AuthPrincipal = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> list[SupportTicket]:
    rows = await db.scalars(
        select(SupportTicket)
        .where(SupportTicket.deleted_at.is_(None))
        .order_by(SupportTicket.created_at.desc())
        .limit(100)
    )
    return list(rows)


@router.post("/tickets", response_model=TicketOut, status_code=201)
async def create_ticket(
    body: TicketIn,
    principal: AuthPrincipal = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> SupportTicket:
    ticket = SupportTicket(
        organization_id=body.organization_id,
        opened_by=principal.user.id,
        subject=body.subject,
        body=body.body,
        priority=body.priority,
        status="open",
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.patch("/tickets/{ticket_id}", response_model=TicketOut)
async def patch_ticket(
    ticket_id: UUID,
    status_value: str = "resolved",
    _: AuthPrincipal = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> SupportTicket:
    ticket = await db.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = status_value
    await db.commit()
    await db.refresh(ticket)
    return ticket
