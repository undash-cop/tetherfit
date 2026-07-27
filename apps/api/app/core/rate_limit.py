from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-process rate limiter (per IP). Suitable for single-replica; Redis later."""

    def __init__(self, app, *, limit: int = 120, window: int = 60) -> None:
        super().__init__(app)
        self.limit = limit
        self.window = window
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in {"/health", "/metrics", "/docs", "/openapi.json", "/redoc"}:
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        now = time.time()
        with self._lock:
            bucket = self._hits[client]
            cutoff = now - self.window
            self._hits[client] = [t for t in bucket if t >= cutoff]
            if len(self._hits[client]) >= self.limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={"Retry-After": str(self.window)},
                )
            self._hits[client].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        return response
