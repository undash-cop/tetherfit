from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import Settings, get_settings


@dataclass
class NotificationMessage:
    channel: str  # email | push | whatsapp | sms
    recipient: str
    subject: str | None
    body: str
    meta: dict | None = None


class NotificationProvider(ABC):
    name: str

    @abstractmethod
    def send(self, message: NotificationMessage) -> str:
        """Return provider status string."""


class NoopNotificationProvider(NotificationProvider):
    name = "noop"

    def send(self, message: NotificationMessage) -> str:
        return "sent"


def get_notification_provider(settings: Settings | None = None) -> NotificationProvider:
    _ = settings or get_settings()
    # Future: Email/WhatsApp/SMS/Push providers selected by channel + env
    return NoopNotificationProvider()
