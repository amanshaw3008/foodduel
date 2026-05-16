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
├── frontend/               # React app for searching and comparing results
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

# 5. Run the frontend in another terminal
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` and search with a PIN code or live browser location.
The frontend proxies `/api` and `/health` requests to `http://127.0.0.1:8000`
in local development. For a deployed API, set `VITE_API_BASE_URL`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service status + API key check |
| GET | `/api/compare` | Compare restaurants across platforms |
| GET | `/api/location/pincode/{pincode}` | Resolve an Indian PIN code to coordinates |
| GET | `/api/photos/google` | Stream live Google Places restaurant photos |
| GET | `/api/photos/cuisine` | Stream live nearby cuisine tile photos |
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

## What's Left To Build

| Next Step | What It Means |
|-----------|---------------|
| React frontend | Build a polished user interface so users can compare food options without reading the API docs |
| Swiggy/Zomato APIs | Replace stubs with real price comparison once platform access is approved |
| Operating hours detail | Return full weekday schedules for each restaurant |
| Custom domain | Point `foodduel.in` to the deployed app instead of the default `onrender.com` URL |

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

## Free Global Hosting

Recommended free setup:

1. Deploy the FastAPI backend on Render from this repository root.
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Set `GOOGLE_PLACES_API_KEY`.
   - Set `ALLOWED_ORIGINS` after the frontend is deployed, for example:
     `["https://your-foodduel-site.vercel.app"]`

2. Deploy the React frontend on Vercel or Netlify with `frontend` as the root directory.
   - Build command: `npm run build`
   - Output directory: `dist`
   - Set `VITE_API_BASE_URL` to the Render backend URL, for example:
     `https://foodduel-api.onrender.com`

3. Redeploy the backend after adding the final frontend URL to `ALLOWED_ORIGINS`.

Redis is optional. Without `REDIS_URL`, the API still runs, but responses are not cached.
