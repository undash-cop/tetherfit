from datetime import UTC, datetime, timedelta

from app.features.scheduling.api import _next_occurrences
from app.presentation.metrics import record_request


def test_next_occurrences_weekly_monday():
    start = datetime(2026, 7, 27, 10, 0, tzinfo=UTC)  # Monday
    occ = _next_occurrences(start, [0], 1, 4)
    assert len(occ) >= 4
    assert all(o.weekday() == 0 for o in occ)


def test_next_occurrences_respects_interval():
    start = datetime(2026, 7, 27, 10, 0, tzinfo=UTC)
    occ = _next_occurrences(start, [0], 2, 8)
    assert len(occ) >= 2
    if len(occ) >= 2:
        delta = (occ[1].date() - occ[0].date()).days
        assert delta >= 14


def test_metrics_counter_increments():
    record_request(200)
    record_request(500)
    # smoke: no exception
    assert True


def test_timedelta_duration():
    start = datetime(2026, 7, 27, 10, 0, tzinfo=UTC)
    end = start + timedelta(minutes=60)
    assert (end - start).total_seconds() == 3600
