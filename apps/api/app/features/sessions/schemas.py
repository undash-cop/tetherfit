from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SessionCreate(BaseModel):
    client_id: UUID
    starts_at: datetime
    ends_at: datetime
    location: str | None = Field(default=None, max_length=255)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_range(self) -> SessionCreate:
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class SessionUpdate(BaseModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    location: str | None = None
    notes: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    client_id: UUID
    trainer_id: UUID
    starts_at: datetime
    ends_at: datetime
    status: str
    location: str | None
    notes: str | None
    check_in_at: datetime | None
    started_at: datetime | None
    paused_at: datetime | None = None
    finished_at: datetime | None
    start_latitude: float | None = None
    start_longitude: float | None = None
    start_accuracy_m: float | None = None
    rating: int | None
    package_id: UUID | None
    credit_deducted: bool
    client_name: str | None = None


class FinishSessionBody(BaseModel):
    notes: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)


class StartSessionBody(BaseModel):
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    accuracy_m: float | None = Field(default=None, ge=0)
    location_label: str | None = Field(default=None, max_length=255)
