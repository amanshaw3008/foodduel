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
        ("Egg Biryani", "Biryani", 249, False),
        ("Paneer Biryani", "Biryani", 259, True),
        ("Chicken 65 Biryani", "Biryani", 349, False),
        ("Family Chicken Biryani", "Family Packs", 699, False),
        ("Family Veg Biryani", "Family Packs", 549, True),
        ("Chicken 65", "Starters", 249, False),
        ("Paneer 65", "Starters", 229, True),
        ("Mirchi Ka Salan", "Sides", 59, True),
        ("Raita", "Sides", 49, True),
        ("Double Ka Meetha", "Desserts", 119, True),
        ("Gulab Jamun", "Desserts", 99, True),
        ("Fresh Lime Soda", "Beverages", 89, True),
    ],
    "pizza": [
        ("Margherita Pizza", "Pizza", 249, True),
        ("Farmhouse Pizza", "Pizza", 349, True),
        ("Chicken Pepperoni Pizza", "Pizza", 429, False),
        ("Veggie Supreme Pizza", "Pizza", 399, True),
        ("Paneer Tikka Pizza", "Pizza", 379, True),
        ("BBQ Chicken Pizza", "Pizza", 449, False),
        ("Peri Peri Chicken Pizza", "Pizza", 459, False),
        ("Cheese Burst Pizza", "Pizza", 389, True),
        ("Garlic Breadsticks", "Sides", 149, True),
        ("Stuffed Garlic Bread", "Sides", 189, True),
        ("Potato Wedges", "Sides", 129, True),
        ("Cheese Dip", "Add-ons", 39, True),
        ("Jalapeno Dip", "Add-ons", 39, True),
        ("Choco Lava Cake", "Desserts", 109, True),
        ("Tiramisu Cup", "Desserts", 159, True),
        ("Pepsi", "Beverages", 69, True),
    ],
    "burger": [
        ("Classic Veg Burger", "Burgers", 149, True),
        ("Crispy Chicken Burger", "Burgers", 199, False),
        ("Cheese Burst Burger", "Burgers", 229, True),
        ("Grilled Chicken Burger", "Burgers", 249, False),
        ("Paneer Royale Burger", "Burgers", 219, True),
        ("Double Patty Burger", "Burgers", 279, False),
        ("Aloo Tikki Burger", "Burgers", 119, True),
        ("Peri Peri Fries", "Sides", 129, True),
        ("Cheese Fries", "Sides", 159, True),
        ("Chicken Nuggets", "Sides", 179, False),
        ("Veg Strips", "Sides", 149, True),
        ("Cold Coffee", "Beverages", 139, True),
        ("Chocolate Shake", "Beverages", 159, True),
        ("Iced Tea", "Beverages", 99, True),
    ],
    "dosa": [
        ("Plain Dosa", "Dosa", 99, True),
        ("Masala Dosa", "Dosa", 139, True),
        ("Ghee Karam Dosa", "Dosa", 169, True),
        ("Mysore Masala Dosa", "Dosa", 169, True),
        ("Paneer Dosa", "Dosa", 189, True),
        ("Onion Rava Dosa", "Dosa", 159, True),
        ("Podi Dosa", "Dosa", 149, True),
        ("Idli Sambar", "Breakfast", 89, True),
        ("Medu Vada", "Breakfast", 99, True),
        ("Idli Vada Combo", "Breakfast", 129, True),
        ("Poori Bhaji", "Breakfast", 129, True),
        ("Upma", "Breakfast", 89, True),
        ("Filter Coffee", "Beverages", 59, True),
        ("Masala Chai", "Beverages", 49, True),
        ("Badam Milk", "Beverages", 89, True),
    ],
    "dessert": [
        ("Chocolate Truffle Slice", "Cakes", 149, True),
        ("Red Velvet Jar", "Desserts", 169, True),
        ("Brownie Sundae", "Ice Cream", 199, True),
        ("Gulab Jamun", "Mithai", 99, True),
        ("Rasmalai", "Mithai", 139, True),
        ("Belgian Waffle", "Waffles", 219, True),
        ("Nutella Waffle", "Waffles", 249, True),
        ("Butterscotch Scoop", "Ice Cream", 109, True),
        ("Tender Coconut Ice Cream", "Ice Cream", 129, True),
        ("Black Forest Pastry", "Cakes", 129, True),
        ("Cheesecake Jar", "Desserts", 229, True),
        ("Kesar Pista Kulfi", "Mithai", 119, True),
        ("Cold Coffee", "Beverages", 139, True),
    ],
    "chinese": [
        ("Veg Hakka Noodles", "Noodles", 199, True),
        ("Chicken Fried Rice", "Rice", 239, False),
        ("Veg Manchurian", "Starters", 219, True),
        ("Chilli Chicken", "Starters", 289, False),
        ("Schezwan Noodles", "Noodles", 229, True),
        ("Chicken Hakka Noodles", "Noodles", 249, False),
        ("Veg Fried Rice", "Rice", 199, True),
        ("Egg Fried Rice", "Rice", 219, False),
        ("Paneer Chilli", "Starters", 249, True),
        ("Crispy Corn", "Starters", 199, True),
        ("Schezwan Sauce", "Add-ons", 35, True),
        ("Spring Rolls", "Starters", 179, True),
        ("Honey Chilli Potato", "Starters", 189, True),
        ("Lemon Iced Tea", "Beverages", 99, True),
    ],
    "north indian": [
        ("Paneer Butter Masala", "Curries", 259, True),
        ("Butter Chicken", "Curries", 329, False),
        ("Dal Makhani", "Curries", 229, True),
        ("Chicken Tikka Masala", "Curries", 349, False),
        ("Kadhai Paneer", "Curries", 279, True),
        ("Chole Masala", "Curries", 219, True),
        ("Malai Kofta", "Curries", 289, True),
        ("Tandoori Roti", "Breads", 35, True),
        ("Garlic Naan", "Breads", 69, True),
        ("Butter Naan", "Breads", 59, True),
        ("Lachha Paratha", "Breads", 69, True),
        ("Jeera Rice", "Rice", 149, True),
        ("Peas Pulao", "Rice", 179, True),
        ("Chicken Tikka", "Starters", 329, False),
        ("Paneer Tikka", "Starters", 289, True),
        ("Sweet Lassi", "Beverages", 99, True),
    ],
    "default": [
        ("Chef Special Meal", "Recommended", 249, False),
        ("Veg Value Bowl", "Meals", 189, True),
        ("Signature Starter", "Starters", 229, False),
        ("Paneer Tikka", "Starters", 249, True),
        ("Butter Naan", "Breads", 59, True),
        ("Fresh Lime Soda", "Beverages", 89, True),
        ("Chicken Meal Box", "Meals", 289, False),
        ("Paneer Meal Box", "Meals", 259, True),
        ("Dal Rice Bowl", "Meals", 179, True),
        ("Crispy Veg Starter", "Starters", 189, True),
        ("Chicken Starter", "Starters", 269, False),
        ("Garlic Naan", "Breads", 69, True),
        ("Jeera Rice", "Rice", 149, True),
        ("Gulab Jamun", "Desserts", 99, True),
        ("Chocolate Brownie", "Desserts", 139, True),
        ("Masala Chaas", "Beverages", 79, True),
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
