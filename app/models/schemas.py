from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Platform(str, Enum):
    SWIGGY = "swiggy"
    ZOMATO = "zomato"
    GOOGLE = "google"


class OperatingHours(BaseModel):
    is_open_now: bool
    weekday_text: List[str] = []  # e.g. ["Monday: 10:00 AM – 11:00 PM", ...]
    opens_at: Optional[str] = None
    closes_at: Optional[str] = None


class PlatformListing(BaseModel):
    platform: Platform
    restaurant_id: Optional[str] = None
    name: str
    cuisine: List[str] = []
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    delivery_time_minutes: Optional[int] = None
    delivery_fee: Optional[float] = None
    minimum_order: Optional[float] = None
    discount_label: Optional[str] = None   # e.g. "60% off up to ₹120"
    deep_link: Optional[str] = None        # Open directly in app
    operating_hours: Optional[OperatingHours] = None
    image_url: Optional[str] = None


class MenuItem(BaseModel):
    id: Optional[str] = None
    name: str
    category: str
    price: float
    is_veg: bool = False
    is_popular: bool = False
    platform: Platform = Platform.GOOGLE


class RestaurantMenuResponse(BaseModel):
    restaurant_name: str
    google_place_id: Optional[str] = None
    source: str
    last_updated: Optional[str] = None
    disclaimer: Optional[str] = None
    items: List[MenuItem]


class UnifiedRestaurant(BaseModel):
    """
    One restaurant entry merging data from both platforms.
    Either or both platform listings may be None if unavailable.
    """
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_place_id: Optional[str] = None
    swiggy: Optional[PlatformListing] = None
    zomato: Optional[PlatformListing] = None
    cheaper_platform: Optional[Platform] = None  # computed field
    estimated_saving: Optional[float] = None


class CompareRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=100, description="Dish or restaurant name")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_meters: int = Field(default=3000, ge=500, le=10000)


class CompareResponse(BaseModel):
    query: str
    location: dict
    cached: bool = False
    total_results: int
    results: List[UnifiedRestaurant]


class RestaurantDetailResponse(BaseModel):
    restaurant: UnifiedRestaurant
    cached: bool = False


class LocationLookupResponse(BaseModel):
    pincode: str
    latitude: float
    longitude: float
    formatted_address: str
    source: str


class ProviderSummary(BaseModel):
    id: Platform
    name: str
    mode: str = "mock"


class CartItemRequest(BaseModel):
    menu_item_id: str = Field(..., min_length=1)
    quantity: int = Field(default=1, ge=1, le=50)


class CartCompareRequest(BaseModel):
    items: List[CartItemRequest] = Field(..., min_length=1)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)


class CartLineItem(BaseModel):
    menu_item_id: str
    name: str
    quantity: int
    unit_price: float
    line_total: float


class CartQuote(BaseModel):
    provider_id: Platform
    provider_name: str
    currency: str = "INR"
    eta_minutes: int
    line_items: List[CartLineItem]
    subtotal: float
    discount: float
    taxes: float
    delivery_fee: float
    platform_fee: float
    total: float


class CartCompareResponse(BaseModel):
    winner: Optional[CartQuote]
    quotes: List[CartQuote]
