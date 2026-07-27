from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PackageCreate(BaseModel):
    total_sessions: int = Field(ge=1, le=500)
    notes: str | None = None
    expires_at: datetime | None = None


class PackageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    client_id: UUID
    total_sessions: int
    remaining_sessions: int
    notes: str | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime
