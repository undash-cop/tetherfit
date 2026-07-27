from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.features.dashboard.schemas import DashboardOut
from app.features.dashboard.services import DashboardService

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
async def get_dashboard(
    principal: AuthPrincipal = Depends(require_permission("reports:view")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> DashboardOut:
    return await DashboardService(db).get(org_id(principal))
