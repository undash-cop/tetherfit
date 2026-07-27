from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    timezone: str


class UserMeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    keycloak_user_id: str
    email: str | None = None
    full_name: str
    avatar: str | None = None
    timezone: str
    onboarding_completed: bool
    org_role: str = "business_owner"
    roles: list[str] = []
    organization_id: UUID | None = None
    organization: OrganizationOut | None = None


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    timezone: str = Field(default="UTC", max_length=64)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    timezone: str | None = Field(default=None, max_length=64)


class HealthComponent(BaseModel):
    status: str
    detail: str | None = None


class HealthOut(BaseModel):
    status: str
    app: str
    components: dict[str, HealthComponent]
