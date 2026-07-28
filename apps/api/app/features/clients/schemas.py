from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


def compute_pt_validity(
    pt_start_at: datetime | None,
    pt_end_at: datetime | None,
    *,
    now: datetime | None = None,
) -> str:
    """Return not_set | upcoming | active | expired."""
    if pt_start_at is None and pt_end_at is None:
        return "not_set"
    current = now or datetime.now(UTC)
    if pt_start_at is not None and current < pt_start_at:
        return "upcoming"
    if pt_end_at is not None and current > pt_end_at:
        return "expired"
    return "active"


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
    pt_start_at: datetime | None = None
    pt_end_at: datetime | None = None

    @model_validator(mode="after")
    def validate_pt_range(self) -> "ClientCreate":
        if (
            self.pt_start_at is not None
            and self.pt_end_at is not None
            and self.pt_end_at < self.pt_start_at
        ):
            raise ValueError("pt_end_at must be on or after pt_start_at")
        return self


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
    pt_start_at: datetime | None = None
    pt_end_at: datetime | None = None

    @model_validator(mode="after")
    def validate_pt_range(self) -> "ClientUpdate":
        if (
            self.pt_start_at is not None
            and self.pt_end_at is not None
            and self.pt_end_at < self.pt_start_at
        ):
            raise ValueError("pt_end_at must be on or after pt_start_at")
        return self


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
    pt_start_at: datetime | None = None
    pt_end_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    joined_on: datetime | None = None
    pt_validity: str = "not_set"
    sessions_completed: int = 0
    amount_paid_paise: int = 0
