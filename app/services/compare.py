import asyncio
import logging
from typing import List, Tuple

from app.models.schemas import UnifiedRestaurant, Platform, PlatformListing
from app.services.swiggy import swiggy_service
from app.services.zomato import zomato_service
from app.services.google_places import search_nearby_restaurants
from app.core.redis import get_cached, set_cached, build_cache_key

logger = logging.getLogger(__name__)


async def compare_restaurants(
    query: str,
    lat: float,
    lng: float,
    radius: int = 3000,
    nocache: bool = False,
) -> Tuple[List[UnifiedRestaurant], bool]:

    cache_key = build_cache_key("compare", query, lat, lng)

    # 1. Try cache first (unless nocache=true)
    if not nocache:
        cached = await get_cached(cache_key)
        if cached:
            logger.info(f"Cache HIT: {cache_key}")
            return [UnifiedRestaurant(**r) for r in cached], True

    logger.info(f"Cache MISS: {cache_key} — fetching live data")

    # 2. Fire all sources concurrently
    swiggy_task = asyncio.create_task(
        swiggy_service.search_restaurants(query, lat, lng, radius)
    )
    zomato_task = asyncio.create_task(
        zomato_service.search_restaurants(query, lat, lng, radius)
    )
    google_task = asyncio.create_task(
        search_nearby_restaurants(query, lat, lng, radius)
    )

    swiggy_results, zomato_results, google_results = await asyncio.gather(
        swiggy_task, zomato_task, google_task,
        return_exceptions=True,
    )

    if isinstance(swiggy_results, Exception):
        logger.error(f"Swiggy task failed: {swiggy_results}")
        swiggy_results = []
    if isinstance(zomato_results, Exception):
        logger.error(f"Zomato task failed: {zomato_results}")
        zomato_results = []
    if isinstance(google_results, Exception):
        logger.error(f"Google task failed: {google_results}")
        google_results = []

    # 3. Merge results
    unified = _merge_results(google_results, swiggy_results, zomato_results)

    # 4. Compute savings
    for restaurant in unified:
        restaurant = _compute_savings(restaurant)

    # 5. Cache and return
    await set_cached(cache_key, [r.model_dump() for r in unified])

    return unified, False


def _merge_results(
    google: List[UnifiedRestaurant],
    swiggy: List[PlatformListing],
    zomato: List[PlatformListing],
) -> List[UnifiedRestaurant]:

    swiggy_by_name = {s.name.lower(): s for s in swiggy}
    zomato_by_name = {z.name.lower(): z for z in zomato}

    merged = []
    for restaurant in google:
        name_key = restaurant.name.lower()
        if name_key in swiggy_by_name:
            restaurant.swiggy = swiggy_by_name[name_key]
        if name_key in zomato_by_name:
            restaurant.zomato = zomato_by_name[name_key]
        merged.append(restaurant)

    return merged


def _compute_savings(restaurant: UnifiedRestaurant) -> UnifiedRestaurant:
    s_fee = restaurant.swiggy.delivery_fee if restaurant.swiggy else None
    z_fee = restaurant.zomato.delivery_fee if restaurant.zomato else None

    if s_fee is not None and z_fee is not None:
        if s_fee < z_fee:
            restaurant.cheaper_platform = Platform.SWIGGY
            restaurant.estimated_saving = z_fee - s_fee
        elif z_fee < s_fee:
            restaurant.cheaper_platform = Platform.ZOMATO
            restaurant.estimated_saving = s_fee - z_fee
        else:
            restaurant.cheaper_platform = None
            restaurant.estimated_saving = 0.0

    return restaurant