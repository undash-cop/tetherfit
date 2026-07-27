import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.rate_limit import RateLimitMiddleware
from app.features.admin.api import router as admin_router
from app.features.ai.api import router as ai_router
from app.features.analytics.api import router as analytics_router
from app.features.assessments.api import router as assessments_router
from app.features.automations.api import router as automations_router
from app.features.billing.api import router as billing_router
from app.features.calendar_integrations.api import router as calendar_integrations_router
from app.features.chat.api import router as chat_router
from app.features.clients.api import router as clients_router
from app.features.dashboard.api import router as dashboard_router
from app.features.enterprise.api import router as enterprise_router
from app.features.marketplace.api import router as marketplace_router
from app.features.media.api import router as media_router
from app.features.nutrition.api import router as nutrition_router
from app.features.packages.api import router as packages_router
from app.features.portal.api import router as portal_router
from app.features.realtime.api import router as realtime_router
from app.features.reports.api import router as reports_router
from app.features.scheduling.api import router as scheduling_router
from app.features.sessions.api import router as sessions_router
from app.features.users.api import router as users_router
from app.features.workouts.api import router as workouts_router
from app.presentation.health import router as health_router
from app.presentation.metrics import record_request
from app.presentation.metrics import router as metrics_router

logger = logging.getLogger("tetherfit.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.6.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware, limit=180, window=60)

    @app.middleware("http")
    async def request_id_and_timing(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = f"{elapsed_ms:.1f}"
        record_request(response.status_code)
        logger.info(
            "%s %s -> %s (%.1fms) rid=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        return response

    app.include_router(health_router)
    app.include_router(metrics_router)
    app.include_router(users_router)
    app.include_router(clients_router)
    app.include_router(packages_router)
    app.include_router(sessions_router)
    app.include_router(dashboard_router)
    app.include_router(workouts_router)
    app.include_router(assessments_router)
    app.include_router(billing_router)
    app.include_router(nutrition_router)
    app.include_router(reports_router)
    app.include_router(ai_router)
    app.include_router(calendar_integrations_router)
    app.include_router(marketplace_router)
    app.include_router(analytics_router)
    app.include_router(enterprise_router)
    app.include_router(portal_router)
    app.include_router(chat_router)
    app.include_router(admin_router)
    app.include_router(media_router)
    app.include_router(scheduling_router)
    app.include_router(automations_router)
    app.include_router(realtime_router)
    return app


app = create_app()
