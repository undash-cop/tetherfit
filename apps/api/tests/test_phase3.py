from datetime import UTC, datetime

from app.infrastructure.ai import NoopAiProvider, get_ai_provider
from app.infrastructure.calendar_ics import build_session_ics


def test_noop_ai_workout():
    provider = NoopAiProvider()
    result = provider.complete("sys", "Generate a workout plan for hypertrophy")
    assert result.provider == "noop"
    assert "items" in result.content or "title" in result.content


def test_get_ai_provider_defaults_noop():
    provider = get_ai_provider()
    assert provider.name in {"noop", "openai_compatible"}


def test_ics_export_contains_vevent():
    ics = build_session_ics(
        sessions=[
            {
                "id": "abc",
                "title": "PT · Ada",
                "description": "scheduled",
                "starts_at": datetime(2026, 7, 28, 10, 0, tzinfo=UTC),
                "ends_at": datetime(2026, 7, 28, 11, 0, tzinfo=UTC),
            }
        ]
    )
    assert "BEGIN:VEVENT" in ics
    assert "PT · Ada" in ics or "PT" in ics
