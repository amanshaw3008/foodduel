from fastapi import APIRouter, HTTPException, Path

from app.models.schemas import LocationLookupResponse
from app.services.google_places import geocode_pincode

router = APIRouter()


@router.get("/location/pincode/{pincode}", response_model=LocationLookupResponse)
async def lookup_pincode(
    pincode: str = Path(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
):
    """
    Resolve an Indian PIN code to latitude and longitude for comparison search.
    """
    location = await geocode_pincode(pincode)
    if not location:
        raise HTTPException(status_code=404, detail="PIN code location not found")

    return LocationLookupResponse(**location)
