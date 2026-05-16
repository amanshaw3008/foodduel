# FoodDuel — Backend API

Swiggy vs Zomato real-time comparison API for Hyderabad.

## Project Structure

```
foodduel/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── core/
│   │   ├── config.py        # Settings & env vars
│   │   └── redis.py         # Redis connection + cache helpers
│   ├── models/
│   │   └── schemas.py       # Pydantic models (UnifiedRestaurant etc.)
│   ├── routers/
│   │   ├── compare.py       # GET /api/compare
│   │   ├── restaurants.py   # GET /api/restaurants/{place_id}
│   │   └── health.py        # GET /health
│   └── services/
│       ├── compare.py       # Orchestrator — concurrent fetch + merge
│       ├── swiggy.py        # Swiggy API integration (stub)
│       ├── zomato.py        # Zomato API integration (stub)
│       └── google_places.py # Google Places fallback (active)
├── tests/
│   └── test_compare.py
├── requirements.txt
└── .env.example
```

## Quick Start

```bash
# 1. Clone and install
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env — add your GOOGLE_PLACES_API_KEY at minimum

# 3. Start Redis (optional but recommended)
docker run -d -p 6379:6379 redis:alpine

# 4. Run the server
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service status + API key check |
| GET | `/api/compare` | Compare restaurants across platforms |
| GET | `/api/restaurants/{place_id}` | Full detail + operating hours |

### Compare Example

```
GET /api/compare?query=biryani&lat=17.4435&lng=78.3772&radius=3000
```

```json
{
  "query": "biryani",
  "cached": false,
  "total_results": 5,
  "results": [
    {
      "name": "Behrouz Biryani",
      "address": "Madhapur, Hi-Tech City",
      "swiggy": {
        "platform": "swiggy",
        "delivery_fee": 25.0,
        "delivery_time_minutes": 30,
        "operating_hours": { "is_open_now": true, ... },
        "deep_link": "swiggy://restaurants/12345"
      },
      "zomato": {
        "platform": "zomato",
        "delivery_fee": 20.0,
        "delivery_time_minutes": 35,
        "operating_hours": { "is_open_now": true, ... },
        "deep_link": "zomato://r/67890"
      },
      "cheaper_platform": "zomato",
      "estimated_saving": 5.0
    }
  ]
}
```

## Current Data Sources

| Source | Status | Notes |
|--------|--------|-------|
| Google Places | ✅ Active | Set `GOOGLE_PLACES_API_KEY` in `.env` |
| Swiggy | ⏳ Pending | Apply at Swiggy Builders Club |
| Zomato | ⏳ Pending | Apply at Zomato Developer Portal |

## Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Deploy (Render + Redis)

1. Push to GitHub
2. Create a new **Web Service** on Render pointing to this repo
3. Add a **Redis** instance on Render (free tier available)
4. Set all env vars from `.env.example` in Render dashboard
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
