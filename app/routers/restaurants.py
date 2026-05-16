from fastapi import APIRouter, HTTPException
from app.models.schemas import RestaurantDetailResponse, UnifiedRestaurant
from app.services.google_places import get_place_details, _map_place_to_unified
from app.core.redis import get_cached, set_cached
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/restaurants/{place_id}", response_model=RestaurantDetailResponse)
async def get_restaurant(place_id: str):
    """
    Get detailed info for a single restaurant including full operating hours.

    place_id: Google Place ID (returned from /api/compare results)
    """
    cache_key = f"foodduel:detail:{place_id}"

    cached = await get_cached(cache_key)
    if cached:
        return RestaurantDetailResponse(
            restaurant=UnifiedRestaurant(**cached),
            cached=True,
        )

    details = await get_place_details(place_id)
    if not details:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    restaurant = _map_place_to_unified(details)
    await set_cached(cache_key, restaurant.model_dump(), ttl=1800)  # 30 min for details

    return RestaurantDetailResponse(restaurant=restaurant, cached=False)
