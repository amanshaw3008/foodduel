from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import RestaurantDetailResponse, RestaurantMenuResponse, UnifiedRestaurant
from app.services.google_places import get_place_details, _map_place_to_unified
from app.services.menus import MENU_DISCLAIMER, build_menu_preview, fallback_menu_updated_at
from app.core.redis import get_cached, set_cached
import logging
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/restaurants/menu", response_model=RestaurantMenuResponse)
async def get_restaurant_menu(
    place_id: Optional[str] = Query(default=None, description="Google Place ID from compare results"),
    restaurant_name: str = Query(..., min_length=1, max_length=160),
    query: str = Query(default="", max_length=100, description="Current dish/cuisine search"),
):
    """
    Return a menu preview for the selected restaurant.

    Until Swiggy/Zomato menu API credentials are available, this endpoint returns
    deterministic cuisine-aware fallback items so the frontend flow can be used.
    """
    cache_key = f"foodduel:menu:{place_id or restaurant_name.lower()}:{query.lower()}"
    cached = await get_cached(cache_key)
    if cached:
        return RestaurantMenuResponse(**cached)

    resolved_name = restaurant_name.strip()
    if place_id:
        try:
            details = await get_place_details(place_id)
            if details and details.get("name"):
                resolved_name = details["name"]
        except Exception as e:
            logger.warning("Place details lookup failed for menu preview: %s", e)

    menu = RestaurantMenuResponse(
        restaurant_name=resolved_name,
        google_place_id=place_id,
        source="estimated_preview",
        last_updated=fallback_menu_updated_at(),
        disclaimer=MENU_DISCLAIMER,
        items=build_menu_preview(resolved_name, query=query, place_id=place_id),
    )
    await set_cached(cache_key, menu.model_dump(), ttl=1800)
    return menu


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
