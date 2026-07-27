from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import User
from app.features.users.repositories import OrganizationRepository
from app.features.users.schemas import (
    OrganizationCreate,
    OrganizationOut,
    OrganizationUpdate,
    UserMeOut,
)


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.orgs = OrganizationRepository(db)

    async def get_me(self, user: User) -> UserMeOut:
        result = await self.db.execute(
            select(User).options(selectinload(User.organization)).where(User.id == user.id)
        )
        loaded = result.scalar_one()
        return UserMeOut.model_validate(loaded)

    async def bootstrap_organization(self, user: User, data: OrganizationCreate) -> UserMeOut:
        if user.organization_id is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already belongs to an organization",
            )
        existing = await self.orgs.get_by_slug(data.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Organization slug already taken",
            )
        await self.orgs.create(data, user)
        user.onboarding_completed = True
        await self.db.flush()
        return await self.get_me(user)

    async def update_organization(self, user: User, data: OrganizationUpdate) -> OrganizationOut:
        if user.organization_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Organization onboarding required",
            )
        org = await self.orgs.get_by_id(user.organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        updated = await self.orgs.update(org, data)
        return OrganizationOut.model_validate(updated)
