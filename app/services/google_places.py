import asyncio
import httpx
import logging
from typing import List, Optional
from urllib.parse import urlencode

from app.core.config import settings
from app.models.schemas import PlatformListing, OperatingHours, Platform, UnifiedRestaurant

logger = logging.getLogger(__name__)

PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACES_DETAIL_URL = "https://maps.googleapis.com/maps/api/place/details/json"
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACE_PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"
MAX_GOOGLE_PLACES_PAGES = 3


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

    places = await _fetch_nearby_place_pages(params)
    return [_map_place_to_unified(place) for place in places]


async def _fetch_nearby_place_pages(params: dict) -> List[dict]:
    """
    Fetch every nearby-search result page Google exposes for the query.

    Google Places nearby search is paginated, so there is no single request
    that returns every result in one response.
    """
    places = []
    next_page_token = None

    async with httpx.AsyncClient(timeout=10.0) as client:
        for page in range(MAX_GOOGLE_PLACES_PAGES):
            request_params = dict(params)
            if next_page_token:
                request_params["pagetoken"] = next_page_token
                await asyncio.sleep(2)

            resp = await client.get(PLACES_NEARBY_URL, params=request_params)
            resp.raise_for_status()
            data = resp.json()

            places.extend(data.get("results", []))
            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break

            logger.info("Fetched Google Places page %s; loading next page", page + 1)

    return places


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


async def geocode_pincode(pincode: str) -> Optional[dict]:
    """Resolve an Indian PIN code to coordinates for restaurant search."""
    normalized = pincode.strip()
    if not normalized.isdigit() or len(normalized) != 6:
        return None

    if not settings.GOOGLE_PLACES_API_KEY:
        return _mock_pincode_location(normalized)

    params = {
        "key": settings.GOOGLE_PLACES_API_KEY,
        "address": f"{normalized}, India",
        "components": f"postal_code:{normalized}|country:IN",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(GEOCODE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return None

    first = results[0]
    location = first.get("geometry", {}).get("location", {})
    lat = location.get("lat")
    lng = location.get("lng")
    if lat is None or lng is None:
        return None

    return {
        "pincode": normalized,
        "latitude": lat,
        "longitude": lng,
        "formatted_address": first.get("formatted_address", f"{normalized}, India"),
        "source": "google_geocoding",
    }


async def fetch_place_photo(photo_reference: str, maxwidth: int = 720) -> Optional[tuple[bytes, str]]:
    """Fetch live Google Place photo bytes without exposing the API key to the browser."""
    if not photo_reference or not settings.GOOGLE_PLACES_API_KEY:
        return None

    params = {
        "key": settings.GOOGLE_PLACES_API_KEY,
        "maxwidth": maxwidth,
        "photo_reference": photo_reference,
    }

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.get(PLACE_PHOTO_URL, params=params)
        resp.raise_for_status()

    content_type = resp.headers.get("content-type", "image/jpeg")
    if not content_type.startswith("image/"):
        return None

    return resp.content, content_type


async def fetch_cuisine_photo(
    query: str,
    lat: float,
    lng: float,
    radius: int = 3000,
    maxwidth: int = 500,
) -> Optional[tuple[bytes, str]]:
    """Fetch a live nearby restaurant photo for a cuisine or dish query."""
    if not query.strip() or not settings.GOOGLE_PLACES_API_KEY:
        return None

    params = {
        "key": settings.GOOGLE_PLACES_API_KEY,
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": "restaurant",
        "keyword": query.strip(),
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(PLACES_NEARBY_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    for place in data.get("results", []):
        photos = place.get("photos") or []
        if photos and photos[0].get("photo_reference"):
            return await fetch_place_photo(photos[0]["photo_reference"], maxwidth)

    return None


def _map_place_to_unified(place: dict) -> UnifiedRestaurant:
    """Map a Google Places API result to our UnifiedRestaurant schema."""
    geometry = place.get("geometry", {}).get("location", {})
    hours_data = place.get("opening_hours", {})

    operating_hours = OperatingHours(
        is_open_now=hours_data.get("open_now", False),
        weekday_text=hours_data.get("weekday_text", []),
    )
    image_url = _build_place_photo_url(place)

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
        image_url=image_url,
    )

    zomato_listing = PlatformListing(
        platform=Platform.ZOMATO,
        name=place.get("name", ""),
        rating=place.get("rating"),
        rating_count=place.get("user_ratings_total"),
        deep_link=_build_zomato_deeplink(place.get("name", "")),
        operating_hours=operating_hours,
        cuisine=place.get("types", []),
        image_url=image_url,
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


def _build_place_photo_url(place: dict) -> Optional[str]:
    photos = place.get("photos") or []
    if not photos:
        return None

    reference = photos[0].get("photo_reference")
    if not reference:
        return None

    return f"/api/photos/google?{urlencode({'reference': reference, 'maxwidth': 720})}"


def _build_swiggy_deeplink(name: str) -> str:
    encoded = name.replace(" ", "%20")
    return f"swiggy://search?query={encoded}"


def _build_zomato_deeplink(name: str) -> str:
    encoded = name.replace(" ", "%20")
    return f"zomato://search?q={encoded}"


def _mock_pincode_location(pincode: str) -> Optional[dict]:
    """Local development fallback for common Hyderabad PIN codes."""
    mock_locations = {
        "500081": (17.4435, 78.3772, "HITEC City, Hyderabad, Telangana 500081"),
        "500032": (17.4401, 78.3489, "Gachibowli, Hyderabad, Telangana 500032"),
        "500084": (17.4645, 78.3667, "Kondapur, Hyderabad, Telangana 500084"),
        "500033": (17.4300, 78.4070, "Jubilee Hills, Hyderabad, Telangana 500033"),
        "500072": (17.4933, 78.3996, "Kukatpally, Hyderabad, Telangana 500072"),
    }

    location = mock_locations.get(pincode)
    if not location:
        return None

    lat, lng, address = location
    return {
        "pincode": pincode,
        "latitude": lat,
        "longitude": lng,
        "formatted_address": address,
        "source": "local_mock",
    }


def _mock_results(query: str, lat: float, lng: float) -> List[UnifiedRestaurant]:
    """
    Mock data for local development when no API key is set.
    Simulates Hi-Tech City restaurants.
    """
    mock_restaurants = [
        {
            "name": "Behrouz Biryani",
            "address": "Madhapur, Hi-Tech City",
            "image_url": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&w=900&q=80",
        },
        {
            "name": "Faasos - Wraps & Rolls",
            "address": "Kondapur, Hi-Tech City",
            "image_url": "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=900&q=80",
        },
        {
            "name": "Box8 - Desi Meals",
            "address": "Hi-Tech City Main Rd",
            "image_url": "https://images.unsplash.com/photo-1543352634-a1c51d9f1fa7?auto=format&fit=crop&w=900&q=80",
        },
        {
            "name": "Wow! Momo",
            "address": "Cyberabad, Hi-Tech City",
            "image_url": "https://images.unsplash.com/photo-1625220194771-7ebdea0b70b9?auto=format&fit=crop&w=900&q=80",
        },
        {
            "name": "Fresh Menu",
            "address": "Gachibowli, Hi-Tech City",
            "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=900&q=80",
        },
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
                image_url=r["image_url"],
            ),
            zomato=PlatformListing(
                platform=Platform.ZOMATO,
                name=r["name"],
                delivery_time_minutes=35,
                delivery_fee=20.0,
                rating=4.1,
                deep_link=_build_zomato_deeplink(r["name"]),
                operating_hours=operating_hours,
                image_url=r["image_url"],
            ),
        ))
    return results
