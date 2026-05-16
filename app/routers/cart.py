from fastapi import APIRouter, HTTPException

from app.models.schemas import CartCompareRequest, CartCompareResponse
from app.services.mock_providers import compare_mock_cart

router = APIRouter()


@router.post("/cart/compare", response_model=CartCompareResponse)
async def compare_cart(request: CartCompareRequest):
    quotes = compare_mock_cart(request)
    if not quotes:
        raise HTTPException(
            status_code=400,
            detail="Cart contains an unknown menu_item_id or invalid item.",
        )

    return CartCompareResponse(winner=quotes[0], quotes=quotes)
