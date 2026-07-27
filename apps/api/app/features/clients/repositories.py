from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Client, SessionPackage


class ClientRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(
        self,
        organization_id: UUID,
        *,
        limit: int,
        offset: int,
        q: str | None = None,
        status: str | None = None,
    ) -> tuple[list[Client], int]:
        filters = [
            Client.organization_id == organization_id,
            Client.deleted_at.is_(None),
        ]
        if status:
            filters.append(Client.status == status)
        if q:
            like = f"%{q.strip()}%"
            filters.append(
                or_(
                    Client.full_name.ilike(like),
                    Client.email.ilike(like),
                    Client.phone.ilike(like),
                )
            )

        total = await self.db.scalar(select(func.count()).select_from(Client).where(*filters))
        result = await self.db.execute(
            select(Client)
            .where(*filters)
            .order_by(Client.full_name.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), int(total or 0)

    async def get(self, organization_id: UUID, client_id: UUID) -> Client | None:
        result = await self.db.execute(
            select(Client).where(
                Client.id == client_id,
                Client.organization_id == organization_id,
                Client.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, organization_id: UUID, **kwargs) -> Client:
        client = Client(organization_id=organization_id, **kwargs)
        self.db.add(client)
        await self.db.flush()
        await self.db.refresh(client)
        return client

    async def soft_delete(self, client: Client) -> None:
        client.deleted_at = datetime.now(UTC)
        await self.db.flush()

    async def remaining_credits(self, organization_id: UUID, client_id: UUID) -> int:
        total = await self.db.scalar(
            select(func.coalesce(func.sum(SessionPackage.remaining_sessions), 0)).where(
                SessionPackage.organization_id == organization_id,
                SessionPackage.client_id == client_id,
                SessionPackage.deleted_at.is_(None),
                SessionPackage.remaining_sessions > 0,
            )
        )
        return int(total or 0)
