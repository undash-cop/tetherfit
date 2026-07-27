from __future__ import annotations

import time
from threading import Lock

from fastapi import APIRouter, Response

router = APIRouter(tags=["metrics"])

_lock = Lock()
_counters: dict[str, float] = {
    "http_requests_total": 0,
    "http_errors_total": 0,
    "started_at": time.time(),
}


def record_request(status_code: int) -> None:
    with _lock:
        _counters["http_requests_total"] += 1
        if status_code >= 500:
            _counters["http_errors_total"] += 1


@router.get("/metrics")
async def prometheus_metrics() -> Response:
    uptime = time.time() - _counters["started_at"]
    body = "\n".join(
        [
            "# HELP tetherfit_http_requests_total Total HTTP requests",
            "# TYPE tetherfit_http_requests_total counter",
            f"tetherfit_http_requests_total {_counters['http_requests_total']}",
            "# HELP tetherfit_http_errors_total Total HTTP 5xx responses",
            "# TYPE tetherfit_http_errors_total counter",
            f"tetherfit_http_errors_total {_counters['http_errors_total']}",
            "# HELP tetherfit_uptime_seconds Process uptime",
            "# TYPE tetherfit_uptime_seconds gauge",
            f"tetherfit_uptime_seconds {uptime:.0f}",
            "",
        ]
    )
    return Response(content=body, media_type="text/plain; version=0.0.4")
