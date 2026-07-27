from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.domain.models import Client, PtSession, RecurrenceRule, SessionStatus, TrainerAvailability

router = APIRouter(prefix="/api/v1", tags=["scheduling"])


class RecurrenceIn(BaseModel):
    client_id: UUID
    frequency: str = Field(default="weekly", pattern="^(weekly|biweekly)$")
    interval: int = Field(default=1, ge=1, le=4)
    byweekday: list[int] = Field(default_factory=lambda: [0])  # 0=Mon
    starts_on: datetime
    ends_on: datetime | None = None
    duration_minutes: int = Field(default=60, ge=15, le=240)
    location: str | None = None
    generate_weeks: int = Field(default=8, ge=1, le=26)


class RecurrenceOut(BaseModel):
    id: UUID
    client_id: UUID
    frequency: str
    interval: int
    byweekday: list
    starts_on: datetime
    ends_on: datetime | None
    duration_minutes: int
    location: str | None
    active: bool
    sessions_created: int = 0

    model_config = {"from_attributes": True}


class AvailabilityIn(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_minute: int = Field(ge=0, le=1439)
    end_minute: int = Field(ge=1, le=1440)
    timezone: str = "UTC"


class AvailabilityOut(BaseModel):
    id: UUID
    weekday: int
    start_minute: int
    end_minute: int
    timezone: str

    model_config = {"from_attributes": True}


def _next_occurrences(
    starts_on: datetime,
    byweekday: list[int],
    interval_weeks: int,
    weeks: int,
) -> list[datetime]:
    """Generate occurrence datetimes for weekly/biweekly rules."""
    out: list[datetime] = []
    cursor = starts_on.astimezone(UTC)
    # Align to first matching weekday
    for _ in range(7):
        if cursor.weekday() in byweekday:
            break
        cursor += timedelta(days=1)
    end = starts_on + timedelta(weeks=weeks)
    while cursor <= end and len(out) < weeks * max(1, len(byweekday)):
        if cursor.weekday() in byweekday:
            # respect interval by week number delta
            week_delta = (cursor.date() - starts_on.astimezone(UTC).date()).days // 7
            if week_delta % interval_weeks == 0:
                out.append(cursor)
        cursor += timedelta(days=1)
    return out


@router.get("/recurrence-rules", response_model=list[RecurrenceOut])
async def list_rules(
    principal: AuthPrincipal = Depends(require_permission("session:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[RecurrenceRule]:
    rows = await db.scalars(
        select(RecurrenceRule).where(
            RecurrenceRule.organization_id == org_id(principal),
            RecurrenceRule.deleted_at.is_(None),
        )
    )
    return list(rows)


@router.post("/recurrence-rules", response_model=RecurrenceOut, status_code=201)
async def create_rule(
    body: RecurrenceIn,
    principal: AuthPrincipal = Depends(require_permission("session:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> RecurrenceOut:
    oid = org_id(principal)
    client = await db.scalar(
        select(Client).where(
            Client.id == body.client_id,
            Client.organization_id == oid,
            Client.deleted_at.is_(None),
        )
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    interval = 2 if body.frequency == "biweekly" else body.interval
    rule = RecurrenceRule(
        organization_id=oid,
        client_id=body.client_id,
        trainer_id=principal.user.id,
        frequency=body.frequency,
        interval=interval,
        byweekday=body.byweekday,
        starts_on=body.starts_on,
        ends_on=body.ends_on,
        duration_minutes=body.duration_minutes,
        location=body.location,
        active=True,
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(rule)
    await db.flush()

    created = 0
    for starts in _next_occurrences(body.starts_on, body.byweekday, interval, body.generate_weeks):
        if body.ends_on and starts > body.ends_on:
            break
        ends = starts + timedelta(minutes=body.duration_minutes)
        db.add(
            PtSession(
                organization_id=oid,
                client_id=body.client_id,
                trainer_id=principal.user.id,
                starts_at=starts,
                ends_at=ends,
                status=SessionStatus.SCHEDULED,
                location=body.location,
                recurrence_rule_id=rule.id,
                created_by=principal.user.id,
                updated_by=principal.user.id,
            )
        )
        created += 1
    await db.commit()
    await db.refresh(rule)
    out = RecurrenceOut.model_validate(rule)
    out.sessions_created = created
    return out


@router.delete("/recurrence-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_rule(
    rule_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("session:cancel")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> None:
    rule = await db.scalar(
        select(RecurrenceRule).where(
            RecurrenceRule.id == rule_id,
            RecurrenceRule.organization_id == org_id(principal),
            RecurrenceRule.deleted_at.is_(None),
        )
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.active = False
    rule.deleted_at = datetime.now(UTC)
    # cancel future generated sessions
    future = await db.scalars(
        select(PtSession).where(
            PtSession.recurrence_rule_id == rule_id,
            PtSession.starts_at >= datetime.now(UTC),
            PtSession.status == SessionStatus.SCHEDULED,
            PtSession.deleted_at.is_(None),
        )
    )
    for s in future:
        s.status = SessionStatus.CANCELLED
    await db.commit()


@router.get("/availability", response_model=list[AvailabilityOut])
async def list_availability(
    principal: AuthPrincipal = Depends(require_permission("session:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[TrainerAvailability]:
    rows = await db.scalars(
        select(TrainerAvailability).where(
            TrainerAvailability.organization_id == org_id(principal),
            TrainerAvailability.user_id == principal.user.id,
            TrainerAvailability.deleted_at.is_(None),
        )
    )
    return list(rows)


@router.put("/availability", response_model=list[AvailabilityOut])
async def replace_availability(
    body: list[AvailabilityIn],
    principal: AuthPrincipal = Depends(require_permission("session:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[TrainerAvailability]:
    oid = org_id(principal)
    existing = await db.scalars(
        select(TrainerAvailability).where(
            TrainerAvailability.organization_id == oid,
            TrainerAvailability.user_id == principal.user.id,
            TrainerAvailability.deleted_at.is_(None),
        )
    )
    now = datetime.now(UTC)
    for row in existing:
        row.deleted_at = now
    created: list[TrainerAvailability] = []
    for slot in body:
        if slot.end_minute <= slot.start_minute:
            raise HTTPException(status_code=400, detail="end_minute must be after start_minute")
        row = TrainerAvailability(
            organization_id=oid,
            user_id=principal.user.id,
            weekday=slot.weekday,
            start_minute=slot.start_minute,
            end_minute=slot.end_minute,
            timezone=slot.timezone,
            created_by=principal.user.id,
            updated_by=principal.user.id,
        )
        db.add(row)
        created.append(row)
    await db.commit()
    for row in created:
        await db.refresh(row)
    return created
