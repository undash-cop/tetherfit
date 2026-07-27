from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Organization, User
from app.features.users.schemas import OrganizationCreate, OrganizationUpdate


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.organization))
            .where(User.id == user_id, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_keycloak_id(self, keycloak_user_id: str) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.organization))
            .where(User.keycloak_user_id == keycloak_user_id, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()


class OrganizationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: OrganizationCreate, owner: User) -> Organization:
        org = Organization(
            name=data.name,
            slug=data.slug,
            timezone=data.timezone,
            working_hours={},
            feature_flags={"ai": True, "marketplace": True, "analytics": True},
            plan="solo",
        )
        self.db.add(org)
        await self.db.flush()
        owner.organization_id = org.id
        owner.org_role = "business_owner"
        await self.db.flush()
        await self.db.refresh(org)
        return org

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self.db.execute(
            select(Organization).where(Organization.slug == slug, Organization.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, org_id) -> Organization | None:
        result = await self.db.execute(
            select(Organization).where(Organization.id == org_id, Organization.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def update(self, org: Organization, data: OrganizationUpdate) -> Organization:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(org, key, value)
        await self.db.flush()
        await self.db.refresh(org)
        return org
