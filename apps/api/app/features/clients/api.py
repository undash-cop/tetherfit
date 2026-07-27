from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.core.pagination import Page
from app.features.clients.schemas import ClientCreate, ClientOut, ClientUpdate
from app.features.clients.services import ClientService

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


@router.get("", response_model=Page[ClientOut])
async def list_clients(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: str | None = None,
    status: str | None = None,
    principal: AuthPrincipal = Depends(require_permission("client:view")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> Page[ClientOut]:
    return await ClientService(db).list_clients(
        org_id(principal), limit=limit, offset=offset, q=q, status_filter=status
    )


@router.post("", response_model=ClientOut, status_code=201)
async def create_client(
    body: ClientCreate,
    principal: AuthPrincipal = Depends(require_permission("client:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> ClientOut:
    return await ClientService(db).create(org_id(principal), body, principal.user.id)


@router.get("/{client_id}", response_model=ClientOut)
async def get_client(
    client_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("client:view")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> ClientOut:
    return await ClientService(db).get(org_id(principal), client_id)


@router.patch("/{client_id}", response_model=ClientOut)
async def update_client(
    client_id: UUID,
    body: ClientUpdate,
    principal: AuthPrincipal = Depends(require_permission("client:update")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> ClientOut:
    return await ClientService(db).update(org_id(principal), client_id, body, principal.user.id)


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("client:delete")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> None:
    await ClientService(db).delete(org_id(principal), client_id)
