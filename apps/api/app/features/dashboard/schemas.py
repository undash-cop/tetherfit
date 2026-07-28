from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.features.clients.schemas import ClientOut
from app.features.sessions.schemas import SessionOut


class DashboardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    today_sessions: list[SessionOut]
    upcoming_sessions: list[SessionOut]
    recent_clients: list[ClientOut]
    generated_at: datetime
