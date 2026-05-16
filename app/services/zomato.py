import httpx
import logging
from typing import List, Optional

from app.core.config import settings
from app.models.schemas import PlatformListing, OperatingHours, Platform

logger = logging.getLogger(__name__)


class ZomatoService:
    """
    Zomato API integration.

    STATUS: Awaiting API access approval from Zomato Developer Portal.
    Once approved, fill in ZOMATO_API_KEY in .env and implement below
    using actual JSON response structure.

    Apply at: https://developers.zomato.com/api
    Note: Zomato's public API has been restricted — a business partnership
    or direct outreach may be required for full access.
    """

    def __init__(self):
        self.api_key = settings.ZOMATO_API_KEY
        self.base_url = settings.ZOMATO_BASE_URL
        self.is_available = bool(self.api_key)

    async def search_restaurants(
        self,
        query: str,
        lat: float,
        lng: float,
        radius: int = 3000,
    ) -> List[PlatformListing]:
        if not self.is_available:
            logger.info("Zomato API key not set — skipping Zomato fetch")
            return []

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    f"{self.base_url}/search",
                    headers={"user-key": self.api_key},
                    params={
                        "q": query,
                        "lat": lat,
                        "lon": lng,
                        "radius": radius,
                        "sort": "rating",
                        "order": "desc",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            # TODO: Replace with actual field mapping once you inspect the
            # real JSON response from Zomato's API.
            # Use: print(json.dumps(data, indent=2)) on first successful call.
            return [self._map_restaurant(r["restaurant"]) for r in data.get("restaurants", [])]

        except httpx.HTTPStatusError as e:
            logger.error(f"Zomato API HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Zomato fetch failed: {e}")
            return []

    def _map_restaurant(self, raw: dict) -> PlatformListing:
        """
        Map raw Zomato API response to PlatformListing.

        ⚠️  Field names below match Zomato's v2.1 public API.
        Update if new API version uses different structure.

        Known Zomato fields: id, name, user_rating.aggregate_rating,
        user_rating.votes, timings, delivery_timings, offers
        """
        timings = raw.get("timings", "")
        operating_hours = OperatingHours(
            is_open_now=self._is_open(timings),
            weekday_text=[timings] if timings else [],
        )

        return PlatformListing(
            platform=Platform.ZOMATO,
            restaurant_id=str(raw.get("id", "")),
            name=raw.get("name", ""),
            rating=float(raw.get("user_rating", {}).get("aggregate_rating", 0) or 0),
            rating_count=raw.get("user_rating", {}).get("votes"),
            delivery_time_minutes=raw.get("order_delivery_time"),
            delivery_fee=raw.get("delivery_fee"),
            discount_label=raw.get("offers", [None])[0] if raw.get("offers") else None,
            deep_link=f"zomato://r/{raw.get('id')}",
            operating_hours=operating_hours,
            image_url=raw.get("thumb"),
        )

    def _is_open(self, timings: str) -> bool:
        """Basic open/closed check — replace with proper time parsing."""
        if not timings:
            return False
        return "closed" not in timings.lower()


zomato_service = ZomatoService()
