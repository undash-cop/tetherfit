from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page, PageMeta
from app.features.clients.repositories import ClientRepository
from app.features.clients.schemas import ClientCreate, ClientOut, ClientUpdate


class ClientService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = ClientRepository(db)

    async def _enrich(self, organization_id: UUID, client) -> ClientOut:
        out = ClientOut.model_validate(client)
        out.joined_on = client.created_at
        out.remaining_credits = await self.repo.remaining_credits(organization_id, client.id)
        out.sessions_completed = await self.repo.sessions_completed(organization_id, client.id)
        out.amount_paid_paise = await self.repo.amount_paid_paise(organization_id, client.id)
        return out

    async def list_clients(
        self,
        organization_id: UUID,
        *,
        limit: int,
        offset: int,
        q: str | None = None,
        status_filter: str | None = None,
    ) -> Page[ClientOut]:
        items, total = await self.repo.list(
            organization_id, limit=limit, offset=offset, q=q, status=status_filter
        )
        outs = [await self._enrich(organization_id, item) for item in items]
        return Page(items=outs, meta=PageMeta(total=total, limit=limit, offset=offset))

    async def get(self, organization_id: UUID, client_id: UUID) -> ClientOut:
        client = await self.repo.get(organization_id, client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        return await self._enrich(organization_id, client)

    async def create(self, organization_id: UUID, data: ClientCreate, actor_id: UUID) -> ClientOut:
        payload = data.model_dump()
        client = await self.repo.create(
            organization_id,
            **payload,
            created_by=actor_id,
            updated_by=actor_id,
        )
        return await self._enrich(organization_id, client)

    async def update(
        self, organization_id: UUID, client_id: UUID, data: ClientUpdate, actor_id: UUID
    ) -> ClientOut:
        client = await self.repo.get(organization_id, client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(client, key, value)
        client.updated_by = actor_id
        await self.repo.db.flush()
        return await self.get(organization_id, client_id)

    async def delete(self, organization_id: UUID, client_id: UUID) -> None:
        client = await self.repo.get(organization_id, client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        await self.repo.soft_delete(client)
