from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Client, PtSession, SessionStatus
from app.features.packages.services import PackageService
from app.features.sessions.schemas import (
    FinishSessionBody,
    SessionCreate,
    SessionOut,
    SessionUpdate,
)


class SessionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.packages = PackageService(db)

    def _to_out(self, session: PtSession) -> SessionOut:
        out = SessionOut.model_validate(session)
        if session.client:
            out.client_name = session.client.full_name
        return out

    async def _get_client(self, organization_id: UUID, client_id: UUID) -> Client:
        result = await self.db.execute(
            select(Client).where(
                Client.id == client_id,
                Client.organization_id == organization_id,
                Client.deleted_at.is_(None),
            )
        )
        client = result.scalar_one_or_none()
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        return client

    async def get(self, organization_id: UUID, session_id: UUID) -> SessionOut:
        result = await self.db.execute(
            select(PtSession)
            .options(selectinload(PtSession.client))
            .where(
                PtSession.id == session_id,
                PtSession.organization_id == organization_id,
                PtSession.deleted_at.is_(None),
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return self._to_out(session)

    async def list_range(
        self,
        organization_id: UUID,
        *,
        start: datetime,
        end: datetime,
        client_id: UUID | None = None,
    ) -> list[SessionOut]:
        filters = [
            PtSession.organization_id == organization_id,
            PtSession.deleted_at.is_(None),
            PtSession.starts_at >= start,
            PtSession.starts_at < end,
        ]
        if client_id:
            filters.append(PtSession.client_id == client_id)
        result = await self.db.execute(
            select(PtSession)
            .options(selectinload(PtSession.client))
            .where(*filters)
            .order_by(PtSession.starts_at.asc())
        )
        return [self._to_out(s) for s in result.scalars().all()]

    async def create(
        self, organization_id: UUID, trainer_id: UUID, data: SessionCreate
    ) -> SessionOut:
        await self._get_client(organization_id, data.client_id)
        session = PtSession(
            organization_id=organization_id,
            client_id=data.client_id,
            trainer_id=trainer_id,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
            location=data.location,
            notes=data.notes,
            status=SessionStatus.SCHEDULED,
            created_by=trainer_id,
            updated_by=trainer_id,
        )
        self.db.add(session)
        await self.db.flush()
        return await self.get(organization_id, session.id)

    async def update(
        self, organization_id: UUID, session_id: UUID, data: SessionUpdate, actor_id: UUID
    ) -> SessionOut:
        result = await self.db.execute(
            select(PtSession).where(
                PtSession.id == session_id,
                PtSession.organization_id == organization_id,
                PtSession.deleted_at.is_(None),
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.status in {SessionStatus.COMPLETED, SessionStatus.CANCELLED}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session is closed")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(session, key, value)
        if session.ends_at <= session.starts_at:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="ends_at must be after starts_at",
            )
        session.updated_by = actor_id
        await self.db.flush()
        return await self.get(organization_id, session_id)

    async def _load(self, organization_id: UUID, session_id: UUID) -> PtSession:
        result = await self.db.execute(
            select(PtSession).where(
                PtSession.id == session_id,
                PtSession.organization_id == organization_id,
                PtSession.deleted_at.is_(None),
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return session

    async def check_in(self, organization_id: UUID, session_id: UUID) -> SessionOut:
        session = await self._load(organization_id, session_id)
        if session.status != SessionStatus.SCHEDULED:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid transition")
        session.status = SessionStatus.CHECKED_IN
        session.check_in_at = datetime.now(UTC)
        await self.db.flush()
        return await self.get(organization_id, session_id)

    async def start(self, organization_id: UUID, session_id: UUID) -> SessionOut:
        session = await self._load(organization_id, session_id)
        if session.status not in {SessionStatus.SCHEDULED, SessionStatus.CHECKED_IN}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid transition")
        session.status = SessionStatus.IN_PROGRESS
        session.started_at = datetime.now(UTC)
        if session.check_in_at is None:
            session.check_in_at = session.started_at
        await self.db.flush()
        return await self.get(organization_id, session_id)

    async def pause(self, organization_id: UUID, session_id: UUID) -> SessionOut:
        session = await self._load(organization_id, session_id)
        if session.status != SessionStatus.IN_PROGRESS:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid transition")
        session.status = SessionStatus.PAUSED
        session.paused_at = datetime.now(UTC)
        await self.db.flush()
        return await self.get(organization_id, session_id)

    async def resume(self, organization_id: UUID, session_id: UUID) -> SessionOut:
        session = await self._load(organization_id, session_id)
        if session.status != SessionStatus.PAUSED:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid transition")
        session.status = SessionStatus.IN_PROGRESS
        session.paused_at = None
        await self.db.flush()
        return await self.get(organization_id, session_id)

    async def finish(
        self, organization_id: UUID, session_id: UUID, body: FinishSessionBody | None = None
    ) -> SessionOut:
        session = await self._load(organization_id, session_id)
        if session.status not in {
            SessionStatus.SCHEDULED,
            SessionStatus.CHECKED_IN,
            SessionStatus.IN_PROGRESS,
            SessionStatus.PAUSED,
        }:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid transition")
        session.status = SessionStatus.COMPLETED
        session.finished_at = datetime.now(UTC)
        if body:
            if body.notes is not None:
                session.notes = body.notes
            if body.rating is not None:
                session.rating = body.rating
        if not session.credit_deducted:
            pkg = await self.packages.deduct_one(organization_id, session.client_id)
            if pkg:
                session.package_id = pkg.id
                session.credit_deducted = True
        await self.db.flush()
        return await self.get(organization_id, session_id)

    async def cancel(self, organization_id: UUID, session_id: UUID) -> SessionOut:
        session = await self._load(organization_id, session_id)
        if session.status in {
            SessionStatus.COMPLETED,
            SessionStatus.CANCELLED,
            SessionStatus.NO_SHOW,
        }:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid transition")
        session.status = SessionStatus.CANCELLED
        await self.db.flush()
        return await self.get(organization_id, session_id)

    async def mark_no_show(self, organization_id: UUID, session_id: UUID) -> SessionOut:
        session = await self._load(organization_id, session_id)
        if session.status not in {
            SessionStatus.SCHEDULED,
            SessionStatus.CHECKED_IN,
        }:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid transition")
        session.status = SessionStatus.NO_SHOW
        await self.db.flush()
        return await self.get(organization_id, session_id)
