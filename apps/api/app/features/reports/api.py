from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.domain.models import Client, Invoice, InvoiceStatus, Payment, PaymentStatus, PtSession

router = APIRouter(prefix="/api/v1", tags=["reports"])


class ReportsOut(BaseModel):
    clients_total: int
    clients_active: int
    sessions_completed_30d: int
    sessions_scheduled_upcoming: int
    revenue_paise_30d: int
    outstanding_paise: int
    generated_at: datetime


@router.get("/reports/summary", response_model=ReportsOut)
async def reports_summary(
    principal: AuthPrincipal = Depends(require_permission("reports:view")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> ReportsOut:
    oid = org_id(principal)
    now = datetime.now(UTC)
    start_30 = now - timedelta(days=30)

    clients_total = await db.scalar(
        select(func.count())
        .select_from(Client)
        .where(Client.organization_id == oid, Client.deleted_at.is_(None))
    )
    clients_active = await db.scalar(
        select(func.count())
        .select_from(Client)
        .where(
            Client.organization_id == oid,
            Client.deleted_at.is_(None),
            Client.status == "active",
        )
    )
    completed = await db.scalar(
        select(func.count())
        .select_from(PtSession)
        .where(
            PtSession.organization_id == oid,
            PtSession.deleted_at.is_(None),
            PtSession.status == "completed",
            PtSession.finished_at >= start_30,
        )
    )
    upcoming = await db.scalar(
        select(func.count())
        .select_from(PtSession)
        .where(
            PtSession.organization_id == oid,
            PtSession.deleted_at.is_(None),
            PtSession.starts_at >= now,
            PtSession.status.in_(["scheduled", "checked_in", "in_progress"]),
        )
    )
    revenue = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount_paise), 0)).where(
            Payment.organization_id == oid,
            Payment.deleted_at.is_(None),
            Payment.status == PaymentStatus.SUCCESS,
            Payment.created_at >= start_30,
        )
    )
    outstanding = await db.scalar(
        select(func.coalesce(func.sum(Invoice.total_paise), 0)).where(
            Invoice.organization_id == oid,
            Invoice.deleted_at.is_(None),
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID]),
        )
    )
    return ReportsOut(
        clients_total=int(clients_total or 0),
        clients_active=int(clients_active or 0),
        sessions_completed_30d=int(completed or 0),
        sessions_scheduled_upcoming=int(upcoming or 0),
        revenue_paise_30d=int(revenue or 0),
        outstanding_paise=int(outstanding or 0),
        generated_at=now,
    )
