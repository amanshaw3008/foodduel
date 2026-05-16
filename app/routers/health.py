from fastapi import APIRouter
from app.core.redis import get_redis
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    redis = get_redis()
    redis_ok = False
    if redis:
        try:
            await redis.ping()
            redis_ok = True
        except Exception:
            pass

    return {
        "status": "ok",
        "env": settings.APP_ENV,
        "redis": "connected" if redis_ok else "unavailable",
        "swiggy_api": "configured" if settings.SWIGGY_API_KEY else "pending",
        "zomato_api": "configured" if settings.ZOMATO_API_KEY else "pending",
        "google_places": "configured" if settings.GOOGLE_PLACES_API_KEY else "not set",
    }
