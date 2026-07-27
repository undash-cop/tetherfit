from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Client, PtSession, SessionPackage
from app.features.clients.schemas import ClientOut
from app.features.dashboard.schemas import CreditSummary, DashboardOut
from app.features.sessions.schemas import SessionOut


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _session_out(self, session: PtSession) -> SessionOut:
        out = SessionOut.model_validate(session)
        if session.client:
            out.client_name = session.client.full_name
        return out

    async def get(self, organization_id: UUID) -> DashboardOut:
        now = datetime.now(UTC)
        start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_today = start_today + timedelta(days=1)
        end_week = start_today + timedelta(days=7)

        today_result = await self.db.execute(
            select(PtSession)
            .options(selectinload(PtSession.client))
            .where(
                PtSession.organization_id == organization_id,
                PtSession.deleted_at.is_(None),
                PtSession.starts_at >= start_today,
                PtSession.starts_at < end_today,
            )
            .order_by(PtSession.starts_at.asc())
        )
        today_sessions = [self._session_out(s) for s in today_result.scalars().all()]

        upcoming_result = await self.db.execute(
            select(PtSession)
            .options(selectinload(PtSession.client))
            .where(
                PtSession.organization_id == organization_id,
                PtSession.deleted_at.is_(None),
                PtSession.starts_at >= end_today,
                PtSession.starts_at < end_week,
            )
            .order_by(PtSession.starts_at.asc())
            .limit(20)
        )
        upcoming_sessions = [self._session_out(s) for s in upcoming_result.scalars().all()]

        clients_result = await self.db.execute(
            select(Client)
            .where(Client.organization_id == organization_id, Client.deleted_at.is_(None))
            .order_by(Client.updated_at.desc())
            .limit(5)
        )
        recent_clients: list[ClientOut] = []
        for client in clients_result.scalars().all():
            out = ClientOut.model_validate(client)
            credits = await self.db.scalar(
                select(func.coalesce(func.sum(SessionPackage.remaining_sessions), 0)).where(
                    SessionPackage.client_id == client.id,
                    SessionPackage.deleted_at.is_(None),
                )
            )
            out.remaining_credits = int(credits or 0)
            recent_clients.append(out)

        credit_rows = await self.db.execute(
            select(
                Client.id,
                Client.full_name,
                func.coalesce(func.sum(SessionPackage.remaining_sessions), 0).label("remaining"),
            )
            .join(SessionPackage, SessionPackage.client_id == Client.id, isouter=True)
            .where(Client.organization_id == organization_id, Client.deleted_at.is_(None))
            .group_by(Client.id, Client.full_name)
            .order_by("remaining")
        )
        low_credit: list[CreditSummary] = []
        total_remaining = 0
        for row in credit_rows.all():
            remaining = int(row.remaining or 0)
            total_remaining += remaining
            if remaining <= 2:
                low_credit.append(
                    CreditSummary(
                        client_id=row.id,
                        client_name=row.full_name,
                        remaining_sessions=remaining,
                    )
                )

        return DashboardOut(
            today_sessions=today_sessions,
            upcoming_sessions=upcoming_sessions,
            recent_clients=recent_clients,
            low_credit_clients=low_credit[:10],
            total_remaining_credits=total_remaining,
            generated_at=now,
        )
