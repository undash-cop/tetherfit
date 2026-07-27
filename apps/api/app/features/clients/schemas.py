from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ClientCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=32)
    status: str = "active"
    goals: str | None = None
    health_history: str | None = None
    medical_notes: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None


class ClientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = None
    phone: str | None = None
    status: str | None = None
    goals: str | None = None
    health_history: str | None = None
    medical_notes: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    tags: list[str] | None = None
    notes: str | None = None


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    full_name: str
    email: str | None
    phone: str | None
    status: str
    goals: str | None
    health_history: str | None
    medical_notes: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    tags: list[str]
    avatar: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    remaining_credits: int | None = None
