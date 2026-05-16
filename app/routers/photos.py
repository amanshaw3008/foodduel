from fastapi import APIRouter, HTTPException, Query, Response
from typing import Optional

from app.services.google_places import fetch_cuisine_photo, fetch_place_photo, geocode_pincode

router = APIRouter()


@router.get("/photos/google")
async def google_place_photo(
    reference: str = Query(..., min_length=1),
    maxwidth: int = Query(default=720, ge=120, le=1600),
):
    """
    Stream a live Google Places photo through FoodDuel.
    """
    photo = await fetch_place_photo(reference, maxwidth)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    content, content_type = photo
    return Response(
        content=content,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/photos/cuisine")
async def cuisine_photo(
    query: str = Query(..., min_length=1, max_length=100),
    pincode: Optional[str] = Query(default=None, min_length=6, max_length=6, pattern=r"^\d{6}$"),
    lat: Optional[float] = Query(default=None, ge=-90, le=90),
    lng: Optional[float] = Query(default=None, ge=-180, le=180),
    radius: int = Query(default=3000, ge=500, le=10000),
    maxwidth: int = Query(default=500, ge=120, le=1600),
):
    """
    Stream a live nearby Google Places photo for a cuisine tile.
    """
    if pincode:
        location = await geocode_pincode(pincode)
        if not location:
            raise HTTPException(status_code=404, detail="PIN code location not found")
        lat = location["latitude"]
        lng = location["longitude"]

    if lat is None or lng is None:
        raise HTTPException(status_code=422, detail="Provide pincode or lat/lng")

    photo = await fetch_cuisine_photo(query, lat, lng, radius, maxwidth)
    if not photo:
        raise HTTPException(status_code=404, detail="Cuisine photo not found")

    content, content_type = photo
    return Response(
        content=content,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )
