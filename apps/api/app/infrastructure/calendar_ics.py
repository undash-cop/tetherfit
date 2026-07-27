from __future__ import annotations

from datetime import UTC, datetime


def format_ics_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.strftime("%Y%m%dT%H%M%SZ")
    return dt.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def build_session_ics(
    *,
    sessions: list[dict],
    calendar_name: str = "TetherFit Sessions",
) -> str:
    """Build a VCALENDAR from session dicts with id/title/starts_at/ends_at/description."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//TetherFit//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(calendar_name)}",
    ]
    for s in sessions:
        uid = str(s.get("id") or s.get("uid") or "session")
        title = _escape(str(s.get("title") or "PT Session"))
        desc = _escape(str(s.get("description") or ""))
        starts = s["starts_at"]
        ends = s.get("ends_at") or starts
        if isinstance(starts, datetime):
            starts = format_ics_datetime(starts)
        if isinstance(ends, datetime):
            ends = format_ics_datetime(ends)
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}@tetherfit",
                f"DTSTAMP:{format_ics_datetime(datetime.now(UTC))}",
                f"DTSTART:{starts}",
                f"DTEND:{ends}",
                f"SUMMARY:{title}",
                f"DESCRIPTION:{desc}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def sync_connection_stub(provider: str, external_calendar_id: str | None) -> dict:
    """Provider-agnostic sync result used until OAuth tokens are wired."""
    return {
        "provider": provider,
        "external_calendar_id": external_calendar_id,
        "pushed": 0,
        "pulled": 0,
        "status": "synced",
        "note": "OAuth push/pull hooks ready; ICS export is the live integration path.",
    }
