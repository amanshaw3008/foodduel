import httpx
import logging
from typing import List
from app.core.config import settings
from app.models.schemas import PlatformListing, OperatingHours, Platform

logger = logging.getLogger(__name__)

SWIGGY_SEARCH_URL = "https://www.swiggy.com/dapi/restaurants/search/v3"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.swiggy.com/",
    "Origin": "https://www.swiggy.com",
}


class SwiggyService:
    def __init__(self):
        self.cookie = settings.SWIGGY_COOKIE
        self.is_available = bool(self.cookie)

    async def search_restaurants(self, query: str, lat: float, lng: float, radius: int = 3000) -> List[PlatformListing]:
        if not self.is_available:
            logger.info("Swiggy cookie not set — skipping")
            return []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    SWIGGY_SEARCH_URL,
                    params={
                        "lat": lat,
                        "lng": lng,
                        "str": query,
                        "submitAction": "ENTER",
                    },
                    headers={**HEADERS, "Cookie": self.cookie},
                )
                resp.raise_for_status()
                data = resp.json()

            # Log raw response for inspection
            import json
            logger.info(f"Swiggy raw response keys: {list(data.keys())}")

            restaurants = (
                data.get("data", {})
                    .get("results", {})
                    .get("restaurants", [])
            )

            if not restaurants:
                # Try alternate path
                restaurants = (
                    data.get("data", {})
                        .get("restaurants", [])
                )

            logger.info(f"Swiggy returned {len(restaurants)} restaurants")
            return [self._map_restaurant(r) for r in restaurants[:10]]

        except Exception as e:
            logger.error(f"Swiggy fetch failed: {e}")
            return []

    def _map_restaurant(self, raw: dict) -> PlatformListing:
        info = raw.get("info", raw)
        sla = info.get("sla", {})
        fee = info.get("feeDetails", {})
        hours = info.get("availability", {})

        operating_hours = OperatingHours(
            is_open_now=hours.get("opened", True),
        )

        restaurant_id = str(info.get("id", ""))
        name = info.get("name", "")

        return PlatformListing(
            platform=Platform.SWIGGY,
            restaurant_id=restaurant_id,
            name=name,
            rating=float(info.get("avgRating", 0) or 0),
            rating_count=info.get("totalRatingsString"),
            delivery_time_minutes=sla.get("deliveryTime"),
            delivery_fee=fee.get("totalFee"),
            discount_label=info.get("aggregatedDiscountInfoV3", {}).get("header"),
            deep_link=f"swiggy://restaurants/{restaurant_id}",
            operating_hours=operating_hours,
            image_url=info.get("cloudinaryImageId"),
        )


swiggy_service = SwiggyService()