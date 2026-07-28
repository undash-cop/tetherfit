from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Client, Invoice, InvoiceStatus, PtSession, SessionStatus


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

    async def sessions_completed(self, organization_id: UUID, client_id: UUID) -> int:
        totals = await self.sessions_completed_map(organization_id, [client_id])
        return totals.get(client_id, 0)

    async def amount_paid_paise(self, organization_id: UUID, client_id: UUID) -> int:
        totals = await self.amount_paid_map(organization_id, [client_id])
        return totals.get(client_id, 0)

    async def sessions_completed_map(
        self, organization_id: UUID, client_ids: list[UUID]
    ) -> dict[UUID, int]:
        if not client_ids:
            return {}
        rows = await self.db.execute(
            select(PtSession.client_id, func.count())
            .where(
                PtSession.organization_id == organization_id,
                PtSession.client_id.in_(client_ids),
                PtSession.deleted_at.is_(None),
                PtSession.status == SessionStatus.COMPLETED,
            )
            .group_by(PtSession.client_id)
        )
        return {row[0]: int(row[1]) for row in rows.all()}

    async def amount_paid_map(
        self, organization_id: UUID, client_ids: list[UUID]
    ) -> dict[UUID, int]:
        """Sum totals from PAID invoices only (payments collected)."""
        if not client_ids:
            return {}
        rows = await self.db.execute(
            select(Invoice.client_id, func.coalesce(func.sum(Invoice.total_paise), 0))
            .where(
                Invoice.organization_id == organization_id,
                Invoice.client_id.in_(client_ids),
                Invoice.deleted_at.is_(None),
                Invoice.status == InvoiceStatus.PAID,
            )
            .group_by(Invoice.client_id)
        )
        return {row[0]: int(row[1] or 0) for row in rows.all()}
