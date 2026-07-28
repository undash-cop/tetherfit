from __future__ import annotations

import logging
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.message import EmailMessage

from app.core.config import Settings, get_settings

logger = logging.getLogger("tetherfit.notifications")


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
        logger.debug(
            "noop notification channel=%s recipient=%s subject=%s",
            message.channel,
            message.recipient,
            message.subject,
        )
        return "sent"


class SmtpEmailProvider(NotificationProvider):
    """SMTP email for channel=email; other channels fall through as noop-sent."""

    name = "smtp"

    def __init__(self, settings: Settings) -> None:
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self.from_addr = settings.smtp_from or settings.smtp_user or "noreply@tetherfit.local"
        self.use_tls = settings.smtp_use_tls

    def send(self, message: NotificationMessage) -> str:
        if message.channel != "email":
            logger.info(
                "smtp provider skipping non-email channel=%s (unimplemented)",
                message.channel,
            )
            return "skipped"
        msg = EmailMessage()
        msg["From"] = self.from_addr
        msg["To"] = message.recipient
        msg["Subject"] = message.subject or "TetherFit"
        msg.set_content(message.body)
        with smtplib.SMTP(self.host, self.port, timeout=30) as smtp:
            if self.use_tls:
                smtp.starttls()
            if self.user:
                smtp.login(self.user, self.password)
            smtp.send_message(msg)
        return "sent"


def get_notification_provider(settings: Settings | None = None) -> NotificationProvider:
    cfg = settings or get_settings()
    if cfg.smtp_host:
        return SmtpEmailProvider(cfg)
    return NoopNotificationProvider()
