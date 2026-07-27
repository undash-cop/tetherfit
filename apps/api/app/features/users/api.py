from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import (
    AuthPrincipal,
    get_auth_principal,
    require_organization,
    require_permission,
)
from app.core.security import get_current_user
from app.domain.models import User
from app.features.users.schemas import (
    OrganizationCreate,
    OrganizationOut,
    OrganizationUpdate,
    UserMeOut,
)
from app.features.users.services import UserService

router = APIRouter(prefix="/api/v1", tags=["users"])


@router.get("/me", response_model=UserMeOut)
async def read_me(
    principal: AuthPrincipal = Depends(get_auth_principal),
    db: AsyncSession = Depends(get_db),
) -> UserMeOut:
    me = await UserService(db).get_me(principal.user)
    roles = sorted(principal.permission_context().roles)
    return UserMeOut(**{**me.model_dump(), "roles": roles})


@router.post("/organizations", response_model=UserMeOut, status_code=201)
async def create_organization(
    body: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserMeOut:
    """Create organization and complete onboarding for the current user."""
    return await UserService(db).bootstrap_organization(current_user, body)


@router.patch("/organizations/me", response_model=OrganizationOut)
async def update_my_organization(
    body: OrganizationUpdate,
    principal: AuthPrincipal = Depends(require_permission("settings:update")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> OrganizationOut:
    return await UserService(db).update_organization(principal.user, body)
