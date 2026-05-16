import redis.asyncio as aioredis
import json
import logging
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


async def init_redis():
    global _redis
    try:
       _redis = await aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
)
        await _redis.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️ Redis unavailable — caching disabled: {e}")
        _redis = None


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()


def get_redis() -> Optional[aioredis.Redis]:
    return _redis


def build_cache_key(prefix: str, query: str, lat: float, lng: float) -> str:
    """
    Round coordinates to ~500m precision so nearby users share cache hits.
    Key format: foodduel:{prefix}:{query}:{lat}:{lng}
    """
    precision = settings.LOCATION_PRECISION
    rounded_lat = round(lat, precision)
    rounded_lng = round(lng, precision)
    safe_query = query.lower().strip().replace(" ", "_")
    return f"foodduel:{prefix}:{safe_query}:{rounded_lat}:{rounded_lng}"


async def get_cached(key: str) -> Optional[Any]:
    if not _redis:
        return None
    try:
        raw = await _redis.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.warning(f"Cache GET failed for {key}: {e}")
        return None


async def set_cached(key: str, value: Any, ttl: int = None) -> bool:
    if not _redis:
        return False
    try:
        ttl = ttl or settings.CACHE_TTL_SECONDS
        await _redis.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.warning(f"Cache SET failed for {key}: {e}")
        return False
