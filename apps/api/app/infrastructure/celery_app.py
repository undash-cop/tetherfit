from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from celery import Celery

from app.core.config import get_settings

logger = logging.getLogger("tetherfit.celery")

settings = get_settings()

celery_app = Celery(
    "tetherfit",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "session-reminders-hourly": {
            "task": "tetherfit.session_reminders",
            "schedule": 3600.0,
        },
        "automations-daily": {
            "task": "tetherfit.run_daily_automations",
            "schedule": 86400.0,
        },
    },
)


@celery_app.task(name="tetherfit.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="tetherfit.session_reminders")
def session_reminders() -> dict:
    """Scan upcoming sessions and enqueue notification stubs.

    Uses sync SQLAlchemy for Celery worker process. Falls back gracefully if DB
    is unreachable so beat does not crash the worker.
    """
    from sqlalchemy import create_engine, select, text
    from sqlalchemy.orm import Session

    from app.domain.models import Client, PtSession
    from app.infrastructure.notifications import NotificationMessage, get_notification_provider

    sync_url = settings.database_url.replace("+asyncpg", "").replace(
        "postgresql+psycopg", "postgresql"
    )
    if "+asyncpg" in settings.database_url:
        sync_url = settings.database_url.replace("postgresql+asyncpg", "postgresql+psycopg")
    try:
        engine = create_engine(sync_url, pool_pre_ping=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("session_reminders: engine failed: %s", exc)
        return {"sent": 0, "error": str(exc)}

    now = datetime.now(UTC)
    window_end = now + timedelta(hours=2)
    sent = 0
    provider = get_notification_provider()
    try:
        with Session(engine) as db:
            rows = db.execute(
                select(PtSession, Client)
                .join(Client, Client.id == PtSession.client_id)
                .where(
                    PtSession.deleted_at.is_(None),
                    PtSession.status == "scheduled",
                    PtSession.starts_at >= now,
                    PtSession.starts_at <= window_end,
                )
            ).all()
            for session, client in rows:
                recipient = client.email or client.phone or "unknown"
                provider.send(
                    NotificationMessage(
                        channel="email" if client.email else "sms",
                        recipient=recipient,
                        subject="Upcoming PT session",
                        body=(
                            f"Reminder: session with {client.full_name} at "
                            f"{session.starts_at.isoformat()}"
                        ),
                    )
                )
                sent += 1
            db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("session_reminders failed: %s", exc)
        return {"sent": sent, "error": str(exc)}
    finally:
        engine.dispose()
    return {"sent": sent, "window_end": window_end.isoformat()}


@celery_app.task(name="tetherfit.run_daily_automations")
def run_daily_automations() -> dict:
    """Run active renewal/birthday campaigns for all orgs (noop provider by default)."""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from app.domain.models import AutomationCampaign

    sync_url = settings.database_url.replace("postgresql+asyncpg", "postgresql+psycopg")
    try:
        engine = create_engine(sync_url, pool_pre_ping=True)
    except Exception as exc:  # noqa: BLE001
        return {"ran": 0, "error": str(exc)}
    ran = 0
    try:
        with Session(engine) as db:
            campaigns = db.scalars(
                select(AutomationCampaign).where(
                    AutomationCampaign.active.is_(True),
                    AutomationCampaign.deleted_at.is_(None),
                    AutomationCampaign.kind.in_(["renewal", "birthday"]),
                )
            ).all()
            for c in campaigns:
                c.last_run_at = datetime.now(UTC)
                ran += 1
            db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("run_daily_automations failed: %s", exc)
        return {"ran": ran, "error": str(exc)}
    finally:
        engine.dispose()
    return {"ran": ran}
