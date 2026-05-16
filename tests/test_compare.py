import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_compare_basic():
    """Test compare endpoint with Hi-Tech City coordinates."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/compare", params={
            "query": "biryani",
            "lat": 17.4435,
            "lng": 78.3772,
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert data["query"] == "biryani"


@pytest.mark.asyncio
async def test_compare_missing_params():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/compare", params={"query": "pizza"})
    assert resp.status_code == 422  # Missing lat/lng


@pytest.mark.asyncio
async def test_compare_invalid_coords():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/compare", params={
            "query": "biryani",
            "lat": 999,   # Invalid
            "lng": 78.37,
        })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_compare_restaurant_closed_on_one_platform():
    """
    Edge case: restaurant closed on one platform but open on another.
    Result should still return with partial data, not crash.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/compare", params={
            "query": "burger",
            "lat": 17.4435,
            "lng": 78.3772,
        })
    assert resp.status_code == 200
    for r in resp.json()["results"]:
        # Both platform fields can be None — that's valid
        assert "swiggy" in r or "zomato" in r
