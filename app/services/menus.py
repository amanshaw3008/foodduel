from datetime import datetime, timezone
from hashlib import sha256
from typing import List, Optional

from app.models.schemas import MenuItem, Platform


MENU_DISCLAIMER = (
    "Live Swiggy/Zomato item menus need approved provider API access. "
    "These fallback prices are cuisine-aware estimates for preview and comparison UX."
)

_CATALOG: dict[str, list[tuple[str, str, int, bool]]] = {
    "biryani": [
        ("Chicken Dum Biryani", "Biryani", 289, False),
        ("Mutton Biryani", "Biryani", 379, False),
        ("Veg Biryani", "Biryani", 229, True),
        ("Double Masala Biryani", "Biryani", 329, False),
        ("Mirchi Ka Salan", "Sides", 59, True),
        ("Double Ka Meetha", "Desserts", 119, True),
    ],
    "pizza": [
        ("Margherita Pizza", "Pizza", 249, True),
        ("Farmhouse Pizza", "Pizza", 349, True),
        ("Chicken Pepperoni Pizza", "Pizza", 429, False),
        ("Garlic Breadsticks", "Sides", 149, True),
        ("Cheese Dip", "Add-ons", 39, True),
        ("Choco Lava Cake", "Desserts", 109, True),
    ],
    "burger": [
        ("Classic Veg Burger", "Burgers", 149, True),
        ("Crispy Chicken Burger", "Burgers", 199, False),
        ("Cheese Burst Burger", "Burgers", 229, True),
        ("Peri Peri Fries", "Sides", 129, True),
        ("Chicken Nuggets", "Sides", 179, False),
        ("Cold Coffee", "Beverages", 139, True),
    ],
    "dosa": [
        ("Plain Dosa", "Dosa", 99, True),
        ("Masala Dosa", "Dosa", 139, True),
        ("Ghee Karam Dosa", "Dosa", 169, True),
        ("Idli Sambar", "Breakfast", 89, True),
        ("Medu Vada", "Breakfast", 99, True),
        ("Filter Coffee", "Beverages", 59, True),
    ],
    "dessert": [
        ("Chocolate Truffle Slice", "Cakes", 149, True),
        ("Red Velvet Jar", "Desserts", 169, True),
        ("Brownie Sundae", "Ice Cream", 199, True),
        ("Gulab Jamun", "Mithai", 99, True),
        ("Rasmalai", "Mithai", 139, True),
        ("Belgian Waffle", "Waffles", 219, True),
    ],
    "chinese": [
        ("Veg Hakka Noodles", "Noodles", 199, True),
        ("Chicken Fried Rice", "Rice", 239, False),
        ("Veg Manchurian", "Starters", 219, True),
        ("Chilli Chicken", "Starters", 289, False),
        ("Schezwan Sauce", "Add-ons", 35, True),
        ("Spring Rolls", "Starters", 179, True),
    ],
    "north indian": [
        ("Paneer Butter Masala", "Curries", 259, True),
        ("Butter Chicken", "Curries", 329, False),
        ("Dal Makhani", "Curries", 229, True),
        ("Tandoori Roti", "Breads", 35, True),
        ("Garlic Naan", "Breads", 69, True),
        ("Jeera Rice", "Rice", 149, True),
    ],
    "default": [
        ("Chef Special Meal", "Recommended", 249, False),
        ("Veg Value Bowl", "Meals", 189, True),
        ("Signature Starter", "Starters", 229, False),
        ("Paneer Tikka", "Starters", 249, True),
        ("Butter Naan", "Breads", 59, True),
        ("Fresh Lime Soda", "Beverages", 89, True),
    ],
}


def build_menu_preview(restaurant_name: str, query: str = "", place_id: Optional[str] = None) -> List[MenuItem]:
    """
    Return a deterministic fallback menu until provider menu APIs are available.
    The same restaurant/query combination receives stable prices across refreshes.
    """
    catalog_key = _choose_catalog(query, restaurant_name)
    seed = int(sha256(f"{place_id or restaurant_name}:{query}".encode()).hexdigest()[:8], 16)
    price_shift = (seed % 7 - 3) * 10
    popular_index = seed % len(_CATALOG[catalog_key])

    items: List[MenuItem] = []
    for index, (name, category, base_price, is_veg) in enumerate(_CATALOG[catalog_key]):
        price = max(39, base_price + price_shift + (index % 3) * 5)
        items.append(
            MenuItem(
                name=name,
                category=category,
                price=float(price),
                is_veg=is_veg,
                is_popular=index == popular_index,
                platform=Platform.GOOGLE,
            )
        )

    return items


def fallback_menu_updated_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def _choose_catalog(query: str, restaurant_name: str) -> str:
    haystack = f"{query} {restaurant_name}".lower()
    for key in _CATALOG:
        if key != "default" and key in haystack:
            return key
    if "noodle" in haystack or "fried rice" in haystack or "manchurian" in haystack:
        return "chinese"
    if "burger" in haystack:
        return "burger"
    if "sweet" in haystack or "cake" in haystack or "ice cream" in haystack:
        return "dessert"
    return "default"
