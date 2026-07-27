from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.domain.models import AutomationCampaign, Client, SessionPackage
from app.infrastructure.notifications import NotificationMessage, get_notification_provider

router = APIRouter(prefix="/api/v1/automations", tags=["automations"])


class CampaignIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    kind: str = Field(pattern="^(renewal|birthday|announcement)$")
    channel: str = "email"
    template_subject: str | None = None
    template_body: str = Field(min_length=3)
    active: bool = True


class CampaignOut(BaseModel):
    id: UUID
    name: str
    kind: str
    channel: str
    template_subject: str | None
    template_body: str
    active: bool
    last_run_at: datetime | None

    model_config = {"from_attributes": True}


class RunOut(BaseModel):
    campaign_id: UUID
    sent: int
    skipped: int


@router.get("/campaigns", response_model=list[CampaignOut])
async def list_campaigns(
    principal: AuthPrincipal = Depends(require_permission("settings:update")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[AutomationCampaign]:
    rows = await db.scalars(
        select(AutomationCampaign).where(
            AutomationCampaign.organization_id == org_id(principal),
            AutomationCampaign.deleted_at.is_(None),
        )
    )
    return list(rows)


@router.post("/campaigns", response_model=CampaignOut, status_code=201)
async def create_campaign(
    body: CampaignIn,
    principal: AuthPrincipal = Depends(require_permission("settings:update")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> AutomationCampaign:
    row = AutomationCampaign(
        organization_id=org_id(principal),
        name=body.name,
        kind=body.kind,
        channel=body.channel,
        template_subject=body.template_subject,
        template_body=body.template_body,
        active=body.active,
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/campaigns/{campaign_id}/run", response_model=RunOut)
async def run_campaign(
    campaign_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("settings:update")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> RunOut:
    oid = org_id(principal)
    campaign = await db.scalar(
        select(AutomationCampaign).where(
            AutomationCampaign.id == campaign_id,
            AutomationCampaign.organization_id == oid,
            AutomationCampaign.deleted_at.is_(None),
        )
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    provider = get_notification_provider()
    sent = 0
    skipped = 0
    clients = list(
        await db.scalars(
            select(Client).where(Client.organization_id == oid, Client.deleted_at.is_(None))
        )
    )
    today = datetime.now(UTC).date()
    for client in clients:
        if campaign.kind == "birthday":
            if not client.date_of_birth:
                skipped += 1
                continue
            dob = client.date_of_birth.astimezone(UTC).date()
            if (dob.month, dob.day) != (today.month, today.day):
                skipped += 1
                continue
        elif campaign.kind == "renewal":
            from sqlalchemy import func

            remaining = await db.scalar(
                select(func.coalesce(func.sum(SessionPackage.remaining_sessions), 0)).where(
                    SessionPackage.client_id == client.id,
                    SessionPackage.deleted_at.is_(None),
                )
            )
            if int(remaining or 0) > 2:
                skipped += 1
                continue
        recipient = client.email or client.phone
        if not recipient:
            skipped += 1
            continue
        body = campaign.template_body.replace("{{name}}", client.full_name)
        provider.send(
            NotificationMessage(
                channel=campaign.channel,
                recipient=recipient,
                subject=campaign.template_subject,
                body=body,
            )
        )
        sent += 1
    campaign.last_run_at = datetime.now(UTC)
    await db.commit()
    return RunOut(campaign_id=campaign.id, sent=sent, skipped=skipped)
