from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page, PageMeta
from app.features.clients.repositories import ClientRepository
from app.features.clients.schemas import (
    ClientCreate,
    ClientOut,
    ClientUpdate,
    compute_pt_validity,
)


class ClientService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = ClientRepository(db)

    def _base_out(self, client) -> ClientOut:
        out = ClientOut.model_validate(client)
        out.joined_on = client.created_at
        out.pt_validity = compute_pt_validity(client.pt_start_at, client.pt_end_at)
        return out

    async def _enrich_many(self, organization_id: UUID, clients: list) -> list[ClientOut]:
        if not clients:
            return []
        ids = [c.id for c in clients]
        completed = await self.repo.sessions_completed_map(organization_id, ids)
        paid = await self.repo.amount_paid_map(organization_id, ids)
        outs: list[ClientOut] = []
        for client in clients:
            out = self._base_out(client)
            out.sessions_completed = completed.get(client.id, 0)
            out.amount_paid_paise = paid.get(client.id, 0)
            outs.append(out)
        return outs

    async def _enrich(self, organization_id: UUID, client) -> ClientOut:
        return (await self._enrich_many(organization_id, [client]))[0]

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
        outs = await self._enrich_many(organization_id, items)
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
        # Cross-field check when only one side is patched
        start = client.pt_start_at
        end = client.pt_end_at
        if start is not None and end is not None and end < start:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="pt_end_at must be on or after pt_start_at",
            )
        client.updated_by = actor_id
        await self.repo.db.flush()
        return await self.get(organization_id, client_id)

    async def delete(self, organization_id: UUID, client_id: UUID) -> None:
        client = await self.repo.get(organization_id, client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        await self.repo.soft_delete(client)
