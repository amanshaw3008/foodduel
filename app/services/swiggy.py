import httpx
import logging
from typing import List, Optional
from app.core.config import settings
from app.models.schemas import PlatformListing, OperatingHours, Platform
from app.services.mock_providers import mock_swiggy_provider

logger = logging.getLogger(__name__)

SWIGGY_SEARCH_URL = "https://www.swiggy.com/dapi/restaurants/search/v3"
SWIGGY_MENU_URL = "https://www.swiggy.com/dapi/menu/pl"

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
        if settings.USE_MOCK_PROVIDERS:
            logger.info("Mock providers enabled — returning mock Swiggy listings")
            return mock_swiggy_provider.search_restaurants(query, lat, lng, radius)

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

            restaurants = (
                data.get("data", {})
                    .get("results", {})
                    .get("restaurants", [])
            )

            if not restaurants:
                restaurants = data.get("data", {}).get("restaurants", [])

            logger.info(f"Swiggy returned {len(restaurants)} restaurants")

            # Fetch details for first 5 restaurants concurrently
            import asyncio
            tasks = [
                self._get_restaurant_with_details(r, lat, lng)
                for r in restaurants[:10]
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if isinstance(r, PlatformListing)]

        except Exception as e:
            logger.error(f"Swiggy fetch failed: {e}")
            return []

    async def _get_restaurant_with_details(self, raw: dict, lat: float, lng: float) -> PlatformListing:
        """Map basic info then enrich with delivery details."""
        listing = self._map_restaurant(raw)

        # Try to get delivery details
        if listing.restaurant_id:
            try:
                details = await self._fetch_menu_details(listing.restaurant_id, lat, lng)
                if details:
                    listing.delivery_time_minutes = details.get("delivery_time")
                    listing.delivery_fee = details.get("delivery_fee")
                    listing.minimum_order = details.get("min_order")
                    listing.discount_label = details.get("discount")
            except Exception as e:
                logger.warning(f"Could not fetch details for {listing.name}: {e}")

        return listing

    async def _fetch_menu_details(self, restaurant_id: str, lat: float, lng: float) -> Optional[dict]:
        """Fetch delivery time and fee from Swiggy menu API."""
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    SWIGGY_MENU_URL,
                    params={
                        "page-type": "REGULAR_MENU",
                        "complete-menu": "true",
                        "lat": lat,
                        "lng": lng,
                        "restaurantId": restaurant_id,
                        "submitAction": "ENTER",
                    },
                    headers={**HEADERS, "Cookie": self.cookie},
                )
                resp.raise_for_status()
                data = resp.json()

            # Navigate to restaurant info
            restaurant_info = (
                data.get("data", {})
                    .get("cards", [{}])[0]
                    .get("card", {})
                    .get("card", {})
                    .get("info", {})
            )

            if not restaurant_info:
                # Try alternate path
                for card in data.get("data", {}).get("cards", []):
                    info = card.get("card", {}).get("card", {}).get("info", {})
                    if info.get("id"):
                        restaurant_info = info
                        break

            sla = restaurant_info.get("sla", {})
            fee = restaurant_info.get("feeDetails", {})
            discount = restaurant_info.get("aggregatedDiscountInfoV3", {})

            delivery_time = sla.get("deliveryTime") or sla.get("slaString")
            delivery_fee_val = fee.get("totalFee") or fee.get("fees", [{}])[0].get("val") if fee.get("fees") else None
            min_order = fee.get("minDeliveryFee")
            discount_label = None
            if discount:
                header = discount.get("header", "")
                sub = discount.get("subHeader", "")
                discount_label = f"{header} {sub}".strip() if header else None

            return {
                "delivery_time": int(delivery_time) if str(delivery_time).isdigit() else None,
                "delivery_fee": float(delivery_fee_val) / 100 if delivery_fee_val else None,
                "min_order": float(min_order) / 100 if min_order else None,
                "discount": discount_label,
            }

        except Exception as e:
            logger.warning(f"Menu fetch failed for {restaurant_id}: {e}")
            return None

    def _map_restaurant(self, raw: dict) -> PlatformListing:
        info = raw.get("info", raw)
        sla = info.get("sla", {})
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
            delivery_fee=None,
            discount_label=None,
            deep_link=f"https://www.swiggy.com/restaurants/{name.lower().replace(' ', '-')}-{restaurant_id}",
            operating_hours=operating_hours,
            image_url=info.get("cloudinaryImageId"),
        )


swiggy_service = SwiggyService()
