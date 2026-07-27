from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Client, SessionPackage
from app.features.packages.schemas import PackageCreate, PackageOut


class PackageService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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

    async def list_for_client(self, organization_id: UUID, client_id: UUID) -> list[PackageOut]:
        await self._get_client(organization_id, client_id)
        result = await self.db.execute(
            select(SessionPackage)
            .where(
                SessionPackage.organization_id == organization_id,
                SessionPackage.client_id == client_id,
                SessionPackage.deleted_at.is_(None),
            )
            .order_by(SessionPackage.created_at.desc())
        )
        return [PackageOut.model_validate(p) for p in result.scalars().all()]

    async def create(
        self, organization_id: UUID, client_id: UUID, data: PackageCreate, actor_id: UUID
    ) -> PackageOut:
        await self._get_client(organization_id, client_id)
        pkg = SessionPackage(
            organization_id=organization_id,
            client_id=client_id,
            total_sessions=data.total_sessions,
            remaining_sessions=data.total_sessions,
            notes=data.notes,
            expires_at=data.expires_at,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(pkg)
        await self.db.flush()
        await self.db.refresh(pkg)
        return PackageOut.model_validate(pkg)

    async def deduct_one(self, organization_id: UUID, client_id: UUID) -> SessionPackage | None:
        """Deduct one credit from the oldest package with remaining sessions."""
        result = await self.db.execute(
            select(SessionPackage)
            .where(
                SessionPackage.organization_id == organization_id,
                SessionPackage.client_id == client_id,
                SessionPackage.deleted_at.is_(None),
                SessionPackage.remaining_sessions > 0,
            )
            .order_by(SessionPackage.created_at.asc())
            .limit(1)
        )
        pkg = result.scalar_one_or_none()
        if not pkg:
            return None
        pkg.remaining_sessions -= 1
        await self.db.flush()
        return pkg
