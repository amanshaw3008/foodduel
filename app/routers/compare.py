from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import CompareResponse
from app.services.compare import compare_restaurants
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/compare", response_model=CompareResponse)
async def compare(
    query: str = Query(..., min_length=1, max_length=100, description="Dish or restaurant name"),
    lat: float = Query(..., ge=-90, le=90, description="User latitude"),
    lng: float = Query(..., ge=-180, le=180, description="User longitude"),
    radius: int = Query(default=3000, ge=500, le=10000, description="Search radius in meters"),
):
    """
    Main comparison endpoint.

    Fires Swiggy + Zomato + Google Places concurrently and returns
    a unified list of restaurants with price comparison and operating hours.

    Example:
        GET /api/compare?query=biryani&lat=17.4435&lng=78.3772&radius=3000
    """
    try:
        results, cached = await compare_restaurants(query, lat, lng, radius)
    except Exception as e:
        logger.error(f"Compare failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch restaurant data")

    return CompareResponse(
        query=query,
        location={"lat": lat, "lng": lng, "radius_meters": radius},
        cached=cached,
        total_results=len(results),
        results=results,
    )
