from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.domain.models import CalendarConnection, Client, PtSession
from app.infrastructure.calendar_ics import build_session_ics, sync_connection_stub

router = APIRouter(prefix="/api/v1", tags=["calendar-integrations"])


class ConnectionIn(BaseModel):
    provider: str = Field(pattern="^(google|outlook|ics)$")
    display_name: str = Field(min_length=1, max_length=255)
    external_calendar_id: str | None = None


class ConnectionOut(BaseModel):
    id: UUID
    provider: str
    display_name: str
    external_calendar_id: str | None
    status: str
    last_synced_at: datetime | None

    model_config = {"from_attributes": True}


@router.get("/calendar-connections", response_model=list[ConnectionOut])
async def list_connections(
    principal: AuthPrincipal = Depends(require_permission("integrations:manage")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[CalendarConnection]:
    oid = org_id(principal)
    rows = await db.scalars(
        select(CalendarConnection).where(
            CalendarConnection.organization_id == oid,
            CalendarConnection.deleted_at.is_(None),
            CalendarConnection.user_id == principal.user.id,
        )
    )
    return list(rows)


@router.post(
    "/calendar-connections",
    response_model=ConnectionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_connection(
    body: ConnectionIn,
    principal: AuthPrincipal = Depends(require_permission("integrations:manage")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> CalendarConnection:
    row = CalendarConnection(
        organization_id=org_id(principal),
        user_id=principal.user.id,
        provider=body.provider,
        display_name=body.display_name,
        external_calendar_id=body.external_calendar_id,
        status="connected",
        meta={},
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/calendar-connections/{connection_id}/sync")
async def sync_connection(
    connection_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("integrations:manage")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> dict:
    oid = org_id(principal)
    row = await db.scalar(
        select(CalendarConnection).where(
            CalendarConnection.id == connection_id,
            CalendarConnection.organization_id == oid,
            CalendarConnection.deleted_at.is_(None),
        )
    )
    if not row:
        raise HTTPException(status_code=404, detail="Connection not found")
    result = sync_connection_stub(row.provider, row.external_calendar_id)
    row.last_synced_at = datetime.now(UTC)
    row.status = "connected"
    row.updated_by = principal.user.id
    await db.commit()
    return result


@router.delete("/calendar-connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("integrations:manage")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> Response:
    oid = org_id(principal)
    row = await db.scalar(
        select(CalendarConnection).where(
            CalendarConnection.id == connection_id,
            CalendarConnection.organization_id == oid,
            CalendarConnection.deleted_at.is_(None),
        )
    )
    if not row:
        raise HTTPException(status_code=404, detail="Connection not found")
    row.deleted_at = datetime.now(UTC)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/calendar/export.ics")
async def export_ics(
    days: int = 60,
    principal: AuthPrincipal = Depends(require_permission("session:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> Response:
    oid = org_id(principal)
    now = datetime.now(UTC)
    end = now + timedelta(days=max(1, min(days, 365)))
    sessions = await db.scalars(
        select(PtSession).where(
            PtSession.organization_id == oid,
            PtSession.deleted_at.is_(None),
            PtSession.starts_at >= now - timedelta(days=7),
            PtSession.starts_at <= end,
            PtSession.status.notin_(["cancelled"]),
        )
    )
    payload = []
    for s in sessions:
        client = await db.get(Client, s.client_id)
        name = client.full_name if client else "Client"
        payload.append(
            {
                "id": s.id,
                "title": f"PT · {name}",
                "description": f"Status: {s.status}",
                "starts_at": s.starts_at,
                "ends_at": s.ends_at,
            }
        )
    ics = build_session_ics(sessions=payload)
    return Response(
        content=ics,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="tetherfit-sessions.ics"'},
    )
