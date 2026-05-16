from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.core.config import settings
from app.core.redis import init_redis, close_redis
from app.routers import compare, restaurants, health, location, photos


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_redis()
    yield
    # Shutdown
    await close_redis()


app = FastAPI(
    title="FoodDuel API",
    description="Real-time Swiggy vs Zomato price & restaurant comparison for Hyderabad",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(compare.router, prefix="/api", tags=["Compare"])
app.include_router(restaurants.router, prefix="/api", tags=["Restaurants"])
app.include_router(location.router, prefix="/api", tags=["Location"])
app.include_router(photos.router, prefix="/api", tags=["Photos"])

frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
frontend_index = frontend_dist / "index.html"
frontend_assets = frontend_dist / "assets"

if frontend_assets.exists():
    app.mount("/assets", StaticFiles(directory=frontend_assets), name="frontend-assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend(full_path: str):
    if frontend_index.exists():
        return FileResponse(frontend_index)

    return {"detail": "Frontend build not found"}
