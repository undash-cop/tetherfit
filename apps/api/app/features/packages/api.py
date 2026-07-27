from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.features.packages.schemas import PackageCreate, PackageOut
from app.features.packages.services import PackageService

router = APIRouter(prefix="/api/v1/clients/{client_id}/packages", tags=["packages"])


@router.get("", response_model=list[PackageOut])
async def list_packages(
    client_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("payment:view")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[PackageOut]:
    return await PackageService(db).list_for_client(org_id(principal), client_id)


@router.post("", response_model=PackageOut, status_code=201)
async def create_package(
    client_id: UUID,
    body: PackageCreate,
    principal: AuthPrincipal = Depends(require_permission("payment:collect")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> PackageOut:
    return await PackageService(db).create(org_id(principal), client_id, body, principal.user.id)
