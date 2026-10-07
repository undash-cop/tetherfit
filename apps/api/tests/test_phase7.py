from datetime import UTC, datetime, timedelta

import pytest

from app.features.billing.api import _compute_tax_paise, _split_inclusive_tax_paise
from app.features.clients.schemas import ClientCreate, ClientUpdate, compute_pt_validity
from app.features.sessions.schemas import StartSessionBody


def test_start_session_body_geo_bounds():
    body = StartSessionBody(latitude=12.97, longitude=77.59, accuracy_m=12.5)
    assert body.latitude == 12.97
    with pytest.raises(ValueError):
        StartSessionBody(latitude=120)


def test_compute_tax_from_default_gst():
    assert (
        _compute_tax_paise(10_000, tax_paise=None, apply_default_gst=True, default_gst_pct=18)
        == 1800
    )
    assert (
        _compute_tax_paise(10_000, tax_paise=500, apply_default_gst=True, default_gst_pct=18) == 500
    )
    assert (
        _compute_tax_paise(10_000, tax_paise=None, apply_default_gst=False, default_gst_pct=18) == 0
    )


def test_split_inclusive_tax_from_gross_amount():
    taxable, tax = _split_inclusive_tax_paise(11_800, 18)
    assert taxable == 10_000
    assert tax == 1_800


def test_pt_validity_states():
    now = datetime(2026, 7, 28, tzinfo=UTC)
    assert compute_pt_validity(None, None, now=now) == "not_set"
    upcoming = compute_pt_validity(now + timedelta(days=1), now + timedelta(days=30), now=now)
    assert upcoming == "upcoming"
    active = compute_pt_validity(now - timedelta(days=10), now + timedelta(days=10), now=now)
    assert active == "active"
    expired = compute_pt_validity(now - timedelta(days=30), now - timedelta(days=1), now=now)
    assert expired == "expired"


def test_client_pt_range_validation():
    start = datetime.now(UTC)
    with pytest.raises(ValueError):
        ClientCreate(
            full_name="A",
            pt_start_at=start,
            pt_end_at=start - timedelta(days=1),
        )
    with pytest.raises(ValueError):
        ClientUpdate(pt_start_at=start, pt_end_at=start - timedelta(days=1))
    ok = ClientCreate(full_name="A", pt_start_at=start, pt_end_at=start + timedelta(days=30))
    assert ok.full_name == "A"
