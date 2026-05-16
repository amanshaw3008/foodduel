from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://yourdomain.com"]

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 900  # 15 minutes

    # Google Places (fallback until Swiggy/Zomato APIs approved)
    GOOGLE_PLACES_API_KEY: str = ""

    # Swiggy (fill once API access is granted)
    SWIGGY_API_KEY: str = ""
    SWIGGY_BASE_URL: str = "https://api.swiggy.com/v1"  # placeholder

    # Zomato (fill once API access is granted)
    ZOMATO_API_KEY: str = ""
    ZOMATO_BASE_URL: str = "https://developers.zomato.com/api/v2.1"  # placeholder

    # Location rounding for cache key (degrees ~ 500m)
    LOCATION_PRECISION: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
