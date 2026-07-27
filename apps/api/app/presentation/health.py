from fastapi import APIRouter

from app.core.config import get_settings
from app.core.database import check_database
from app.features.users.schemas import HealthComponent, HealthOut
from app.infrastructure.r2 import check_r2_configured
from app.infrastructure.redis_client import check_redis

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    settings = get_settings()
    db_ok = await check_database()
    redis_ok = await check_redis()
    r2_ok, r2_detail = check_r2_configured(settings)

    components = {
        "database": HealthComponent(
            status="up" if db_ok else "down",
            detail=None if db_ok else "Unable to reach PostgreSQL",
        ),
        "redis": HealthComponent(
            status="up" if redis_ok else "down",
            detail=None if redis_ok else "Unable to reach Redis",
        ),
        "r2": HealthComponent(
            status="up" if r2_ok else "degraded",
            detail=r2_detail if not r2_ok else None,
        ),
    }

    critical_ok = db_ok  # API can run without redis/r2 briefly; DB is required
    return HealthOut(
        status="ok" if critical_ok else "degraded",
        app=settings.app_name,
        components=components,
    )
