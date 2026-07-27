from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.domain.models import Client, Payment, PaymentStatus, PtSession, User

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


class Point(BaseModel):
    date: date
    value: int


class AnalyticsOut(BaseModel):
    revenue_series: list[Point]
    sessions_series: list[Point]
    client_growth_series: list[Point]
    completion_rate_pct: float
    no_show_rate_pct: float
    active_trainers: int
    generated_at: datetime


@router.get("/overview", response_model=AnalyticsOut)
async def analytics_overview(
    days: int = 30,
    principal: AuthPrincipal = Depends(require_permission("analytics:view")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOut:
    oid = org_id(principal)
    days = max(7, min(days, 90))
    now = datetime.now(UTC)
    start = now - timedelta(days=days)

    revenue_rows = await db.execute(
        select(
            cast(Payment.created_at, Date).label("d"),
            func.coalesce(func.sum(Payment.amount_paise), 0),
        )
        .where(
            Payment.organization_id == oid,
            Payment.deleted_at.is_(None),
            Payment.status == PaymentStatus.SUCCESS,
            Payment.created_at >= start,
        )
        .group_by("d")
        .order_by("d")
    )
    session_rows = await db.execute(
        select(
            cast(PtSession.starts_at, Date).label("d"),
            func.count(),
        )
        .where(
            PtSession.organization_id == oid,
            PtSession.deleted_at.is_(None),
            PtSession.starts_at >= start,
        )
        .group_by("d")
        .order_by("d")
    )
    client_rows = await db.execute(
        select(
            cast(Client.created_at, Date).label("d"),
            func.count(),
        )
        .where(
            Client.organization_id == oid,
            Client.deleted_at.is_(None),
            Client.created_at >= start,
        )
        .group_by("d")
        .order_by("d")
    )

    completed = await db.scalar(
        select(func.count())
        .select_from(PtSession)
        .where(
            PtSession.organization_id == oid,
            PtSession.deleted_at.is_(None),
            PtSession.status == "completed",
            PtSession.starts_at >= start,
        )
    )
    no_shows = await db.scalar(
        select(func.count())
        .select_from(PtSession)
        .where(
            PtSession.organization_id == oid,
            PtSession.deleted_at.is_(None),
            PtSession.status == "no_show",
            PtSession.starts_at >= start,
        )
    )
    total_closed = int(completed or 0) + int(no_shows or 0)
    completion = (100.0 * int(completed or 0) / total_closed) if total_closed else 0.0
    no_show_rate = (100.0 * int(no_shows or 0) / total_closed) if total_closed else 0.0

    trainers = await db.scalar(
        select(func.count())
        .select_from(User)
        .where(
            User.organization_id == oid,
            User.deleted_at.is_(None),
        )
    )

    return AnalyticsOut(
        revenue_series=[Point(date=r[0], value=int(r[1])) for r in revenue_rows],
        sessions_series=[Point(date=r[0], value=int(r[1])) for r in session_rows],
        client_growth_series=[Point(date=r[0], value=int(r[1])) for r in client_rows],
        completion_rate_pct=round(completion, 1),
        no_show_rate_pct=round(no_show_rate, 1),
        active_trainers=int(trainers or 0),
        generated_at=now,
    )
