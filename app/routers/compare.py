from fastapi import APIRouter, HTTPException, Query, Response
from app.models.schemas import CompareResponse
from app.services.compare import compare_restaurants
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/compare", response_model=CompareResponse)
async def compare(
    response: Response,
    query: str = Query(..., min_length=1, max_length=100, description="Dish or restaurant name"),
    lat: float = Query(..., ge=-90, le=90, description="User latitude"),
    lng: float = Query(..., ge=-180, le=180, description="User longitude"),
    radius: int = Query(default=3000, ge=500, le=10000, description="Search radius in meters"),
    nocache: bool = Query(default=False, description="Bypass cache for fresh results"),
):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"

    try:
        results, cached = await compare_restaurants(query, lat, lng, radius, nocache=nocache)
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
