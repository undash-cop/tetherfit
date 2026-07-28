from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Client, PtSession
from app.features.clients.schemas import ClientOut, compute_pt_validity
from app.features.dashboard.schemas import DashboardOut
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
            out.joined_on = client.created_at
            out.pt_validity = compute_pt_validity(client.pt_start_at, client.pt_end_at)
            recent_clients.append(out)

        return DashboardOut(
            today_sessions=today_sessions,
            upcoming_sessions=upcoming_sessions,
            recent_clients=recent_clients,
            generated_at=now,
        )
