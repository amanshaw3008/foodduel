from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Union

from app.models.schemas import (
    CartCompareRequest,
    CartLineItem,
    CartQuote,
    MenuItem,
    OperatingHours,
    Platform,
    PlatformListing,
    UnifiedRestaurant,
)


@dataclass(frozen=True)
class CatalogItem:
    id: str
    name: str
    category: str
    base_price: float
    is_veg: bool
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class CatalogRestaurant:
    id: str
    name: str
    address: str
    cuisine: tuple[str, ...]
    rating: float
    rating_count: int
    latitude_offset: float
    longitude_offset: float
    image_url: str
    menu_item_ids: tuple[str, ...]


class FoodProvider(ABC):
    id: Platform
    name: str

    @abstractmethod
    def search_restaurants(
        self,
        query: str,
        lat: float,
        lng: float,
        radius: int = 3000,
    ) -> List[PlatformListing]:
        raise NotImplementedError

    @abstractmethod
    def get_menu(self, restaurant_id: str) -> Optional[List[MenuItem]]:
        raise NotImplementedError

    @abstractmethod
    def price_cart(self, request: CartCompareRequest) -> Optional[CartQuote]:
        raise NotImplementedError


class MockFoodProvider(FoodProvider):
    def __init__(
        self,
        provider_id: Platform,
        name: str,
        price_multiplier: float,
        delivery_fee: float,
        platform_fee: float,
        eta_minutes: int,
        discount_percent: float,
    ):
        self.id = provider_id
        self.name = name
        self.price_multiplier = price_multiplier
        self.delivery_fee = delivery_fee
        self.platform_fee = platform_fee
        self.eta_minutes = eta_minutes
        self.discount_percent = discount_percent

    def search_restaurants(
        self,
        query: str,
        lat: float,
        lng: float,
        radius: int = 3000,
    ) -> List[PlatformListing]:
        return [
            self._restaurant_listing(restaurant)
            for restaurant in _matching_restaurants(query, lat, lng)
        ]

    def get_menu(self, restaurant_id: str) -> Optional[List[MenuItem]]:
        restaurant = _restaurant_by_id(restaurant_id)
        if not restaurant:
            return None

        return [
            self._menu_item(_MENU_BY_ID[item_id])
            for item_id in restaurant.menu_item_ids
        ]

    def price_cart(self, request: CartCompareRequest) -> Optional[CartQuote]:
        line_items: list[CartLineItem] = []
        for request_item in request.items:
            catalog_item = _MENU_BY_ID.get(request_item.menu_item_id)
            if not catalog_item:
                return None

            unit_price = self._provider_price(catalog_item.base_price)
            line_items.append(
                CartLineItem(
                    menu_item_id=catalog_item.id,
                    name=catalog_item.name,
                    quantity=request_item.quantity,
                    unit_price=unit_price,
                    line_total=unit_price * request_item.quantity,
                )
            )

        subtotal = sum(item.line_total for item in line_items)
        discount = round(subtotal * self.discount_percent, 2)
        taxes = round((subtotal - discount) * 0.05, 2)
        total = round(subtotal - discount + taxes + self.delivery_fee + self.platform_fee, 2)

        return CartQuote(
            provider_id=self.id,
            provider_name=self.name,
            eta_minutes=self.eta_minutes,
            line_items=line_items,
            subtotal=subtotal,
            discount=discount,
            taxes=taxes,
            delivery_fee=self.delivery_fee,
            platform_fee=self.platform_fee,
            total=total,
        )

    def _restaurant_listing(self, restaurant: CatalogRestaurant) -> PlatformListing:
        return PlatformListing(
            platform=self.id,
            restaurant_id=restaurant.id,
            name=restaurant.name,
            cuisine=list(restaurant.cuisine),
            rating=restaurant.rating,
            rating_count=restaurant.rating_count,
            delivery_time_minutes=self.eta_minutes,
            delivery_fee=self.delivery_fee,
            minimum_order=99.0,
            discount_label=f"{int(self.discount_percent * 100)}% off on mock orders",
            deep_link=f"{self.id.value}://restaurants/{restaurant.id}",
            operating_hours=OperatingHours(
                is_open_now=True,
                weekday_text=["Monday - Sunday: 10:00 AM - 11:00 PM"],
            ),
            image_url=restaurant.image_url,
        )

    def _menu_item(self, item: CatalogItem) -> MenuItem:
        return MenuItem(
            id=item.id,
            name=item.name,
            category=item.category,
            price=self._provider_price(item.base_price),
            is_veg=item.is_veg,
            is_popular=item.id in {"chicken-biryani", "margherita-pizza", "classic-burger"},
            platform=self.id,
        )

    def _provider_price(self, base_price: float) -> float:
        return float(max(1, round(base_price * self.price_multiplier)))


_MENU_ITEMS = [
    CatalogItem("classic-burger", "Classic Burger", "Burgers", 189, False, ("burger", "fast food")),
    CatalogItem("classic-fries", "Classic Fries", "Sides", 99, True, ("fries", "burger")),
    CatalogItem("choco-shake", "Chocolate Shake", "Beverages", 149, True, ("shake", "dessert")),
    CatalogItem("margherita-pizza", "Margherita Pizza", "Pizza", 249, True, ("pizza", "italian")),
    CatalogItem("peri-peri-pizza", "Peri Peri Pizza", "Pizza", 309, True, ("pizza", "spicy")),
    CatalogItem("garlic-bread", "Garlic Bread", "Sides", 129, True, ("pizza", "bread")),
    CatalogItem("masala-dosa", "Masala Dosa", "South Indian", 119, True, ("dosa", "breakfast")),
    CatalogItem("idli-vada-combo", "Idli Vada Combo", "Breakfast", 99, True, ("idli", "dosa")),
    CatalogItem("filter-coffee", "Filter Coffee", "Beverages", 49, True, ("coffee", "breakfast")),
    CatalogItem("chicken-biryani", "Chicken Biryani", "Biryani", 269, False, ("biryani", "chicken")),
    CatalogItem("paneer-biryani", "Paneer Biryani", "Biryani", 239, True, ("biryani", "paneer")),
    CatalogItem("gulab-jamun", "Gulab Jamun", "Desserts", 79, True, ("dessert", "sweet")),
    CatalogItem("butter-chicken", "Butter Chicken", "North Indian", 329, False, ("north indian", "chicken")),
    CatalogItem("paneer-butter-masala", "Paneer Butter Masala", "North Indian", 259, True, ("north indian", "paneer")),
    CatalogItem("dal-makhani", "Dal Makhani", "North Indian", 229, True, ("north indian", "dal")),
    CatalogItem("garlic-naan", "Garlic Naan", "Breads", 69, True, ("north indian", "naan")),
    CatalogItem("veg-hakka-noodles", "Veg Hakka Noodles", "Chinese", 199, True, ("chinese", "noodles")),
    CatalogItem("chicken-fried-rice", "Chicken Fried Rice", "Chinese", 239, False, ("chinese", "fried rice")),
    CatalogItem("chilli-chicken", "Chilli Chicken", "Chinese", 289, False, ("chinese", "starter")),
    CatalogItem("veg-manchurian", "Veg Manchurian", "Chinese", 219, True, ("chinese", "manchurian")),
    CatalogItem("red-velvet-jar", "Red Velvet Jar", "Desserts", 169, True, ("dessert", "cake")),
    CatalogItem("brownie-sundae", "Brownie Sundae", "Desserts", 199, True, ("dessert", "ice cream")),
    CatalogItem("belgian-waffle", "Belgian Waffle", "Desserts", 219, True, ("dessert", "waffle")),
    CatalogItem("rasmalai", "Rasmalai", "Desserts", 139, True, ("dessert", "sweet")),
    CatalogItem("chicken-roll", "Chicken Roll", "Rolls", 179, False, ("roll", "street food")),
    CatalogItem("paneer-roll", "Paneer Roll", "Rolls", 159, True, ("roll", "street food")),
    CatalogItem("momos", "Steamed Momos", "Momos", 139, False, ("momos", "snack")),
    CatalogItem("veg-momos", "Veg Momos", "Momos", 119, True, ("momos", "snack")),
    CatalogItem("vada-pav", "Vada Pav", "Street Food", 69, True, ("street food", "mumbai")),
    CatalogItem("pav-bhaji", "Pav Bhaji", "Street Food", 149, True, ("street food", "mumbai")),
    CatalogItem("kathi-roll", "Kathi Roll", "Rolls", 169, False, ("rolls", "kolkata")),
    CatalogItem("fish-curry", "Fish Curry", "Meals", 279, False, ("seafood", "bengali")),
    CatalogItem("chicken-chettinad", "Chicken Chettinad", "South Indian", 299, False, ("south indian", "chicken")),
]

_MENU_BY_ID = {item.id: item for item in _MENU_ITEMS}

_RESTAURANTS = [
    CatalogRestaurant(
        id="burger-barn-hitech-city",
        name="Burger Barn",
        address="Madhapur, Hi-Tech City",
        cuisine=("Burgers", "American", "Fast Food"),
        rating=4.4,
        rating_count=1200,
        latitude_offset=0.001,
        longitude_offset=0.001,
        image_url="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("classic-burger", "classic-fries", "choco-shake"),
    ),
    CatalogRestaurant(
        id="pizza-yard-kondapur",
        name="Pizza Yard",
        address="Kondapur, Hyderabad",
        cuisine=("Pizza", "Italian"),
        rating=4.2,
        rating_count=940,
        latitude_offset=0.002,
        longitude_offset=-0.001,
        image_url="https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("margherita-pizza", "peri-peri-pizza", "garlic-bread"),
    ),
    CatalogRestaurant(
        id="dosa-district-gachibowli",
        name="Dosa District",
        address="Gachibowli, Hyderabad",
        cuisine=("South Indian", "Breakfast"),
        rating=4.6,
        rating_count=1500,
        latitude_offset=-0.001,
        longitude_offset=0.002,
        image_url="https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("masala-dosa", "idli-vada-combo", "filter-coffee"),
    ),
    CatalogRestaurant(
        id="biryani-box-madhapur",
        name="Biryani Box",
        address="Madhapur, Hyderabad",
        cuisine=("Biryani", "North Indian"),
        rating=4.3,
        rating_count=2100,
        latitude_offset=0.003,
        longitude_offset=0.001,
        image_url="https://images.unsplash.com/photo-1563379091339-03246963d96c?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("chicken-biryani", "paneer-biryani", "gulab-jamun"),
    ),
    CatalogRestaurant(
        id="greenchillyz-old-town",
        name="GreenChillyz Old Town",
        address="Lewis Road, Bhubaneswar",
        cuisine=("Biryani", "Tandoor", "North Indian"),
        rating=4.4,
        rating_count=1729,
        latitude_offset=0.002,
        longitude_offset=0.003,
        image_url="https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("chicken-biryani", "paneer-biryani", "butter-chicken", "garlic-naan", "gulab-jamun"),
    ),
    CatalogRestaurant(
        id="truptee-veg-bhubaneswar",
        name="Truptee Veg Restaurant",
        address="Bapuji Nagar, Bhubaneswar",
        cuisine=("North Indian", "South Indian", "Pure Veg"),
        rating=4.1,
        rating_count=8339,
        latitude_offset=0.001,
        longitude_offset=-0.002,
        image_url="https://images.unsplash.com/photo-1543352634-a1c51d9f1fa7?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("masala-dosa", "idli-vada-combo", "paneer-butter-masala", "dal-makhani", "filter-coffee"),
    ),
    CatalogRestaurant(
        id="lemon-mustard-bhubaneswar",
        name="Lemon Mustard",
        address="Old Town, Bhubaneswar",
        cuisine=("Chinese", "North Indian", "Biryani"),
        rating=4.3,
        rating_count=410,
        latitude_offset=-0.002,
        longitude_offset=0.002,
        image_url="https://images.unsplash.com/photo-1526318896980-cf78c088247c?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("veg-hakka-noodles", "chicken-fried-rice", "chilli-chicken", "chicken-biryani", "brownie-sundae"),
    ),
    CatalogRestaurant(
        id="bangalore-dosa-co-indiranagar",
        name="Bangalore Dosa Co.",
        address="Indiranagar, Bengaluru",
        cuisine=("South Indian", "Breakfast", "Coffee"),
        rating=4.7,
        rating_count=2340,
        latitude_offset=0.001,
        longitude_offset=0.001,
        image_url="https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("masala-dosa", "idli-vada-combo", "filter-coffee"),
    ),
    CatalogRestaurant(
        id="koramangala-pizza-lab",
        name="Koramangala Pizza Lab",
        address="Koramangala, Bengaluru",
        cuisine=("Pizza", "Italian", "Fast Food"),
        rating=4.3,
        rating_count=1880,
        latitude_offset=-0.002,
        longitude_offset=0.002,
        image_url="https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("margherita-pizza", "peri-peri-pizza", "garlic-bread", "brownie-sundae"),
    ),
    CatalogRestaurant(
        id="delhi-butter-chicken-house",
        name="Delhi Butter Chicken House",
        address="Connaught Place, New Delhi",
        cuisine=("North Indian", "Mughlai", "Biryani"),
        rating=4.5,
        rating_count=3210,
        latitude_offset=0.001,
        longitude_offset=-0.001,
        image_url="https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("butter-chicken", "dal-makhani", "garlic-naan", "chicken-biryani", "rasmalai"),
    ),
    CatalogRestaurant(
        id="gurgaon-burger-desk",
        name="Gurgaon Burger Desk",
        address="Cyber Hub, Gurugram",
        cuisine=("Burgers", "Fast Food", "American"),
        rating=4.2,
        rating_count=1480,
        latitude_offset=-0.003,
        longitude_offset=0.002,
        image_url="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("classic-burger", "classic-fries", "choco-shake", "momos"),
    ),
    CatalogRestaurant(
        id="mumbai-vada-pav-corner",
        name="Mumbai Vada Pav Corner",
        address="Dadar, Mumbai",
        cuisine=("Street Food", "Snacks", "Maharashtrian"),
        rating=4.6,
        rating_count=4100,
        latitude_offset=0.001,
        longitude_offset=0.001,
        image_url="https://images.unsplash.com/photo-1606491956689-2ea866880c84?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("vada-pav", "pav-bhaji", "veg-momos", "filter-coffee"),
    ),
    CatalogRestaurant(
        id="bandra-dessert-studio",
        name="Bandra Dessert Studio",
        address="Bandra West, Mumbai",
        cuisine=("Desserts", "Waffles", "Ice Cream"),
        rating=4.4,
        rating_count=980,
        latitude_offset=-0.002,
        longitude_offset=-0.001,
        image_url="https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("red-velvet-jar", "brownie-sundae", "belgian-waffle", "choco-shake"),
    ),
    CatalogRestaurant(
        id="chennai-chettinad-kitchen",
        name="Chennai Chettinad Kitchen",
        address="T Nagar, Chennai",
        cuisine=("South Indian", "Chettinad", "Biryani"),
        rating=4.4,
        rating_count=1890,
        latitude_offset=0.001,
        longitude_offset=0.001,
        image_url="https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("chicken-chettinad", "masala-dosa", "chicken-biryani", "filter-coffee"),
    ),
    CatalogRestaurant(
        id="kolkata-roll-house",
        name="Kolkata Roll House",
        address="Park Street, Kolkata",
        cuisine=("Rolls", "Street Food", "Bengali"),
        rating=4.5,
        rating_count=2650,
        latitude_offset=0.001,
        longitude_offset=0.001,
        image_url="https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=900&q=80",
        menu_item_ids=("kathi-roll", "chicken-roll", "paneer-roll", "fish-curry", "rasmalai"),
    ),
]

mock_swiggy_provider = MockFoodProvider(
    provider_id=Platform.SWIGGY,
    name="Swiggy Mock",
    price_multiplier=0.98,
    delivery_fee=38.0,
    platform_fee=7.0,
    eta_minutes=24,
    discount_percent=0.05,
)

mock_zomato_provider = MockFoodProvider(
    provider_id=Platform.ZOMATO,
    name="Zomato Mock",
    price_multiplier=1.03,
    delivery_fee=32.0,
    platform_fee=6.0,
    eta_minutes=28,
    discount_percent=0.08,
)

mock_providers: tuple[MockFoodProvider, ...] = (mock_swiggy_provider, mock_zomato_provider)


def get_mock_provider(provider_id: Union[Platform, str]) -> Optional[MockFoodProvider]:
    normalized = provider_id.value if isinstance(provider_id, Platform) else provider_id
    return next((provider for provider in mock_providers if provider.id.value == normalized), None)


def compare_mock_cart(request: CartCompareRequest) -> list[CartQuote]:
    return sorted(
        [
            quote
            for provider in mock_providers
            if (quote := provider.price_cart(request)) is not None
        ],
        key=lambda quote: quote.total,
    )


def mock_unified_restaurants(query: str, lat: float, lng: float) -> List[UnifiedRestaurant]:
    swiggy_by_name = {
        item.name.lower(): item
        for item in mock_swiggy_provider.search_restaurants(query, lat, lng)
    }
    zomato_by_name = {
        item.name.lower(): item
        for item in mock_zomato_provider.search_restaurants(query, lat, lng)
    }

    results: list[UnifiedRestaurant] = []
    for restaurant in _matching_restaurants(query, lat, lng):
        results.append(
            UnifiedRestaurant(
                name=restaurant.name,
                address=restaurant.address,
                latitude=lat + restaurant.latitude_offset,
                longitude=lng + restaurant.longitude_offset,
                google_place_id=f"mock-{restaurant.id}",
                swiggy=swiggy_by_name.get(restaurant.name.lower()),
                zomato=zomato_by_name.get(restaurant.name.lower()),
            )
        )

    return results


def _matching_restaurants(query: str, lat: float = 17.4435, lng: float = 78.3772) -> List[CatalogRestaurant]:
    normalized = query.strip().lower()
    nearby_restaurants = _restaurants_for_location(lat, lng)
    if not normalized:
        return nearby_restaurants

    matches = []
    for restaurant in nearby_restaurants:
        menu_items = [_MENU_BY_ID[item_id] for item_id in restaurant.menu_item_ids]
        searchable = " ".join(
            [
                restaurant.name,
                restaurant.address,
                *restaurant.cuisine,
                *[item.name for item in menu_items],
                *[keyword for item in menu_items for keyword in item.keywords],
            ]
        ).lower()
        if normalized in searchable:
            matches.append(restaurant)

    return matches or nearby_restaurants


def _restaurants_for_location(lat: float, lng: float) -> List[CatalogRestaurant]:
    city_keywords = _city_keywords_for_location(lat, lng)
    local = [
        restaurant
        for restaurant in _RESTAURANTS
        if any(keyword in restaurant.address.lower() for keyword in city_keywords)
    ]
    generic = [
        restaurant
        for restaurant in _RESTAURANTS
        if not any(city in restaurant.address.lower() for city in _ALL_CITY_KEYWORDS)
    ]
    return local + generic if local else _RESTAURANTS


def _restaurant_by_id(restaurant_id: str) -> Optional[CatalogRestaurant]:
    return next((restaurant for restaurant in _RESTAURANTS if restaurant.id == restaurant_id), None)


def _city_keywords_for_location(lat: float, lng: float) -> tuple[str, ...]:
    if 19.8 <= lat <= 20.6 and 85.4 <= lng <= 86.2:
        return ("bhubaneswar",)
    if 12.5 <= lat <= 13.4 and 77.2 <= lng <= 78.0:
        return ("bengaluru",)
    if 28.2 <= lat <= 29.1 and 76.7 <= lng <= 77.6:
        return ("delhi", "gurugram")
    if 18.7 <= lat <= 19.4 and 72.6 <= lng <= 73.2:
        return ("mumbai",)
    if 12.7 <= lat <= 13.3 and 79.9 <= lng <= 80.5:
        return ("chennai",)
    if 22.3 <= lat <= 23.0 and 88.0 <= lng <= 88.7:
        return ("kolkata",)
    if 17.0 <= lat <= 17.8 and 78.0 <= lng <= 78.8:
        return ("hyderabad",)
    return ()


_ALL_CITY_KEYWORDS = (
    "bhubaneswar",
    "bengaluru",
    "delhi",
    "gurugram",
    "mumbai",
    "chennai",
    "kolkata",
    "hyderabad",
)
