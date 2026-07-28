import pytest

from app.features.billing.api import _build_upi_uri, _compute_tax_paise
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


def test_build_upi_uri():
    uri = _build_upi_uri(vpa="trainer@upi", amount_paise=250000, note="TF-00001")
    assert uri.startswith("upi://pay?")
    assert "pa=trainer" in uri
    assert "am=2500.00" in uri
