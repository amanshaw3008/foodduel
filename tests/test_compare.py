import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.routers import photos
from app.services import google_places


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
    assert data["total_results"] >= 1


@pytest.mark.asyncio
async def test_compare_mock_mode_returns_provider_ids_and_fees():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/compare", params={
            "query": "biryani",
            "lat": 20.2352035,
            "lng": 85.8340168,
            "nocache": True,
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["results"]
    first = data["results"][0]
    assert first["swiggy"]["restaurant_id"]
    assert first["swiggy"]["delivery_time_minutes"]
    assert isinstance(first["swiggy"]["delivery_fee"], float)


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
async def test_vercel_origin_is_allowed_by_cors():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.options(
            "/api/compare",
            headers={
                "Origin": "https://foodduel.vercel.app",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "https://foodduel.vercel.app"


@pytest.mark.asyncio
async def test_lookup_pincode_basic():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/location/pincode/500081")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pincode"] == "500081"
    assert data["latitude"]
    assert data["longitude"]


@pytest.mark.asyncio
async def test_lookup_pincode_invalid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/location/pincode/abc")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_google_places_fetches_paginated_results(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self.payload

    class FakeClient:
        def __init__(self, timeout):
            self.calls = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, params):
            self.calls.append(params)
            if len(self.calls) == 1:
                return FakeResponse({
                    "results": [{"name": "A"}, {"name": "B"}],
                    "next_page_token": "next-page",
                })
            return FakeResponse({"results": [{"name": "C"}]})

    client = FakeClient(timeout=10.0)

    def fake_client_factory(timeout):
        return client

    async def fake_sleep(seconds):
        return None

    monkeypatch.setattr(google_places.httpx, "AsyncClient", fake_client_factory)
    monkeypatch.setattr(google_places.asyncio, "sleep", fake_sleep)

    results = await google_places._fetch_nearby_place_pages({"key": "test"})

    assert [place["name"] for place in results] == ["A", "B", "C"]
    assert client.calls[1]["pagetoken"] == "next-page"


def test_google_place_photo_url_uses_foodduel_proxy():
    url = google_places._build_place_photo_url({
        "photos": [{"photo_reference": "photo ref/with spaces"}]
    })

    assert url.startswith("/api/photos/google?")
    assert "reference=photo+ref%2Fwith+spaces" in url
    assert "key=" not in url


@pytest.mark.asyncio
async def test_google_place_photo_endpoint_streams_image(monkeypatch):
    async def fake_fetch_place_photo(reference, maxwidth):
        assert reference == "abc"
        assert maxwidth == 720
        return b"image-bytes", "image/jpeg"

    monkeypatch.setattr(photos, "fetch_place_photo", fake_fetch_place_photo)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/photos/google", params={"reference": "abc"})

    assert resp.status_code == 200
    assert resp.content == b"image-bytes"
    assert resp.headers["content-type"] == "image/jpeg"


@pytest.mark.asyncio
async def test_cuisine_photo_endpoint_uses_pincode_location(monkeypatch):
    async def fake_geocode_pincode(pincode):
        assert pincode == "500081"
        return {
            "latitude": 17.4435,
            "longitude": 78.3772,
        }

    async def fake_fetch_cuisine_photo(query, lat, lng, radius, maxwidth):
        assert query == "korean"
        assert lat == 17.4435
        assert lng == 78.3772
        assert radius == 3000
        assert maxwidth == 500
        return b"cuisine-image", "image/webp"

    monkeypatch.setattr(photos, "geocode_pincode", fake_geocode_pincode)
    monkeypatch.setattr(photos, "fetch_cuisine_photo", fake_fetch_cuisine_photo)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/photos/cuisine", params={
            "query": "korean",
            "pincode": "500081",
        })

    assert resp.status_code == 200
    assert resp.content == b"cuisine-image"
    assert resp.headers["content-type"] == "image/webp"


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


@pytest.mark.asyncio
async def test_providers_endpoint_lists_mock_providers():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/providers")

    assert resp.status_code == 200
    data = resp.json()
    assert {provider["id"] for provider in data} == {"swiggy", "zomato"}
    expected_mode = "mock" if settings.USE_MOCK_PROVIDERS else "official"
    assert all(provider["mode"] == expected_mode for provider in data)


@pytest.mark.asyncio
async def test_provider_menu_endpoint_returns_item_ids():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/providers/swiggy/restaurants/pizza-yard-kondapur/menu"
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "swiggy_mock"
    assert data["items"][0]["id"]
    assert data["items"][0]["platform"] == "swiggy"


@pytest.mark.asyncio
async def test_restaurant_menu_endpoint_returns_expanded_menu():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/restaurants/menu",
            params={"restaurant_name": "Biryani Box", "query": "biryani"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "estimated_preview"
    assert len(data["items"]) >= 12
    assert len({item["category"] for item in data["items"]}) >= 4


@pytest.mark.asyncio
async def test_cart_compare_returns_sorted_quotes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/cart/compare",
            json={
                "items": [
                    {"menu_item_id": "margherita-pizza", "quantity": 1},
                    {"menu_item_id": "classic-fries", "quantity": 2},
                ],
                "latitude": 17.4435,
                "longitude": 78.3772,
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    totals = [quote["total"] for quote in data["quotes"]]
    assert totals == sorted(totals)
    assert data["winner"]["total"] == totals[0]


@pytest.mark.asyncio
async def test_cart_compare_rejects_unknown_items():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/cart/compare",
            json={"items": [{"menu_item_id": "not-real", "quantity": 1}]},
        )

    assert resp.status_code == 400
