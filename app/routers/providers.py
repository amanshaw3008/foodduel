from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.models.schemas import Platform, ProviderSummary, RestaurantMenuResponse
from app.services.mock_providers import get_mock_provider, mock_providers

router = APIRouter()


@router.get("/providers", response_model=list[ProviderSummary])
async def list_providers():
    mode = "mock" if settings.USE_MOCK_PROVIDERS else "official"
    return [
        ProviderSummary(id=provider.id, name=provider.name, mode=mode)
        for provider in mock_providers
    ]


@router.get(
    "/providers/{provider_id}/restaurants/{restaurant_id}/menu",
    response_model=RestaurantMenuResponse,
)
async def get_provider_restaurant_menu(provider_id: Platform, restaurant_id: str):
    provider = get_mock_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    menu_items = provider.get_menu(restaurant_id)
    if menu_items is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return RestaurantMenuResponse(
        restaurant_name=restaurant_id.replace("-", " ").title(),
        source=f"{provider.id.value}_mock",
        disclaimer="Mock provider menu for local FoodDuel development.",
        items=menu_items,
    )
