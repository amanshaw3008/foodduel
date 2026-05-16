import httpx
import logging
from typing import List, Optional

from app.core.config import settings
from app.models.schemas import PlatformListing, OperatingHours, Platform, UnifiedRestaurant

logger = logging.getLogger(__name__)

PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACES_DETAIL_URL = "https://maps.googleapis.com/maps/api/place/details/json"


async def search_nearby_restaurants(
    query: str,
    lat: float,
    lng: float,
    radius: int = 3000,
) -> List[UnifiedRestaurant]:
    """
    Search Google Places for restaurants matching the query near the given location.
    Used as the primary data source until Swiggy/Zomato APIs are available.
    """
    if not settings.GOOGLE_PLACES_API_KEY:
        logger.warning("GOOGLE_PLACES_API_KEY not set — returning mock data")
        return _mock_results(query, lat, lng)

    params = {
        "key": settings.GOOGLE_PLACES_API_KEY,
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": "restaurant",
        "keyword": query,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(PLACES_NEARBY_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for place in data.get("results", [])[:10]:
        unified = _map_place_to_unified(place)
        results.append(unified)

    return results


async def get_place_details(place_id: str) -> Optional[dict]:
    """Fetch full details including opening hours for a specific place."""
    if not settings.GOOGLE_PLACES_API_KEY:
        return None

    params = {
        "key": settings.GOOGLE_PLACES_API_KEY,
        "place_id": place_id,
        "fields": "name,opening_hours,formatted_address,geometry,rating,user_ratings_total,photos",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(PLACES_DETAIL_URL, params=params)
        resp.raise_for_status()
        return resp.json().get("result", {})


def _map_place_to_unified(place: dict) -> UnifiedRestaurant:
    """Map a Google Places API result to our UnifiedRestaurant schema."""
    geometry = place.get("geometry", {}).get("location", {})
    hours_data = place.get("opening_hours", {})

    operating_hours = OperatingHours(
        is_open_now=hours_data.get("open_now", False),
        weekday_text=hours_data.get("weekday_text", []),
    )

    # Build placeholder platform listings
    # These will be replaced by real Swiggy/Zomato data once APIs are approved
    swiggy_listing = PlatformListing(
        platform=Platform.SWIGGY,
        name=place.get("name", ""),
        rating=place.get("rating"),
        rating_count=place.get("user_ratings_total"),
        deep_link=_build_swiggy_deeplink(place.get("name", "")),
        operating_hours=operating_hours,
        cuisine=place.get("types", []),
    )

    zomato_listing = PlatformListing(
        platform=Platform.ZOMATO,
        name=place.get("name", ""),
        rating=place.get("rating"),
        rating_count=place.get("user_ratings_total"),
        deep_link=_build_zomato_deeplink(place.get("name", "")),
        operating_hours=operating_hours,
        cuisine=place.get("types", []),
    )

    return UnifiedRestaurant(
        name=place.get("name", ""),
        address=place.get("vicinity", ""),
        latitude=geometry.get("lat"),
        longitude=geometry.get("lng"),
        google_place_id=place.get("place_id"),
        swiggy=swiggy_listing,
        zomato=zomato_listing,
    )


def _build_swiggy_deeplink(name: str) -> str:
    encoded = name.replace(" ", "%20")
    return f"swiggy://search?query={encoded}"


def _build_zomato_deeplink(name: str) -> str:
    encoded = name.replace(" ", "%20")
    return f"zomato://search?q={encoded}"


def _mock_results(query: str, lat: float, lng: float) -> List[UnifiedRestaurant]:
    """
    Mock data for local development when no API key is set.
    Simulates Hi-Tech City restaurants.
    """
    mock_restaurants = [
        {"name": "Behrouz Biryani", "address": "Madhapur, Hi-Tech City"},
        {"name": "Faasos - Wraps & Rolls", "address": "Kondapur, Hi-Tech City"},
        {"name": "Box8 - Desi Meals", "address": "Hi-Tech City Main Rd"},
        {"name": "Wow! Momo", "address": "Cyberabad, Hi-Tech City"},
        {"name": "Fresh Menu", "address": "Gachibowli, Hi-Tech City"},
    ]

    results = []
    for r in mock_restaurants:
        operating_hours = OperatingHours(is_open_now=True, weekday_text=["Monday - Sunday: 10:00 AM – 11:00 PM"])
        results.append(UnifiedRestaurant(
            name=r["name"],
            address=r["address"],
            latitude=lat + 0.001,
            longitude=lng + 0.001,
            swiggy=PlatformListing(
                platform=Platform.SWIGGY,
                name=r["name"],
                delivery_time_minutes=30,
                delivery_fee=25.0,
                rating=4.2,
                deep_link=_build_swiggy_deeplink(r["name"]),
                operating_hours=operating_hours,
            ),
            zomato=PlatformListing(
                platform=Platform.ZOMATO,
                name=r["name"],
                delivery_time_minutes=35,
                delivery_fee=20.0,
                rating=4.1,
                deep_link=_build_zomato_deeplink(r["name"]),
                operating_hours=operating_hours,
            ),
        ))
    return results
