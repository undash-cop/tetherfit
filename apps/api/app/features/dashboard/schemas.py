from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.features.clients.schemas import ClientOut
from app.features.sessions.schemas import SessionOut


class CreditSummary(BaseModel):
    client_id: UUID
    client_name: str
    remaining_sessions: int


class DashboardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    today_sessions: list[SessionOut]
    upcoming_sessions: list[SessionOut]
    recent_clients: list[ClientOut]
    low_credit_clients: list[CreditSummary]
    total_remaining_credits: int
    generated_at: datetime
