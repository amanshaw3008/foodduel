import httpx
import logging
from typing import List, Optional

from app.core.config import settings
from app.models.schemas import PlatformListing, OperatingHours, Platform

logger = logging.getLogger(__name__)


class SwiggyService:
    """
    Swiggy API integration.

    STATUS: Awaiting API access approval from Swiggy Builders Club.
    Once approved, fill in SWIGGY_API_KEY and SWIGGY_BASE_URL in .env
    and implement the methods below using their actual JSON response structure.

    Docs: https://developer.swiggy.com (pending access)
    """

    def __init__(self):
        self.api_key = settings.SWIGGY_API_KEY
        self.base_url = settings.SWIGGY_BASE_URL
        self.is_available = bool(self.api_key)

    async def search_restaurants(
        self,
        query: str,
        lat: float,
        lng: float,
        radius: int = 3000,
    ) -> List[PlatformListing]:
        if not self.is_available:
            logger.info("Swiggy API key not set — skipping Swiggy fetch")
            return []

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    f"{self.base_url}/restaurants/search",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={
                        "query": query,
                        "lat": lat,
                        "lng": lng,
                        "radius": radius,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            # TODO: Replace with actual field mapping once you inspect the
            # real JSON response from Swiggy's API.
            # Use: print(json.dumps(data, indent=2)) on first successful call.
            return [self._map_restaurant(r) for r in data.get("data", {}).get("restaurants", [])]

        except httpx.HTTPStatusError as e:
            logger.error(f"Swiggy API HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Swiggy fetch failed: {e}")
            return []

    def _map_restaurant(self, raw: dict) -> PlatformListing:
        """
        Map raw Swiggy API response to PlatformListing.

        ⚠️  Field names below are GUESSES — update after inspecting real API response.
        Common Swiggy fields: id, name, avgRating, totalRatingsString,
        sla.deliveryTime, feeDetails.totalFee, aggregatedDiscountInfo
        """
        hours_raw = raw.get("availability", {})
        operating_hours = OperatingHours(
            is_open_now=hours_raw.get("opened", False),
            weekday_text=hours_raw.get("scheduledSlot", []),
        )

        return PlatformListing(
            platform=Platform.SWIGGY,
            restaurant_id=str(raw.get("id", "")),
            name=raw.get("name", ""),
            rating=float(raw.get("avgRating", 0) or 0),
            rating_count=raw.get("totalRatingsString"),
            delivery_time_minutes=raw.get("sla", {}).get("deliveryTime"),
            delivery_fee=raw.get("feeDetails", {}).get("totalFee"),
            discount_label=raw.get("aggregatedDiscountInfo", {}).get("header"),
            deep_link=f"swiggy://restaurants/{raw.get('id')}",
            operating_hours=operating_hours,
            image_url=raw.get("cloudinaryImageId"),
        )


swiggy_service = SwiggyService()
