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
    USE_MOCK_PROVIDERS: bool = False

    # Swiggy (fill once API access is granted)
    SWIGGY_API_KEY: str = ""
    SWIGGY_COOKIE: str = "deviceId=s%3Ae70bc5de-f711-49d3-b392-b6a4bdd9037a.PR7BfP5cuTQ5YxvQwXhzFmlOSTCJ6eU4I7iLGR8cnpw; tid=a571a969-edaa-49b3-851a-bacec2811c60; sid=s%3Areae8f35b4a-06fe-4122-940d-8e2689d24.VdQ2jP5Yy6QY27wq5aGIV5%2Bu1agWV%2BpdMoBubwvANtY; versionCode=1200; platform=web; subplatform=dweb; statusBarHeight=0; bottomOffset=0; genieTrackOn=false; ally-on=false; isNative=false; strId=; openIMHP=false; lat=s%3A12.960059122809971.h096G6jFEvdKvA%2FcX99%2BU8AUppIjzSJe1T91Va8STTA; lng=s%3A77.57337538383284.wugDnemZ%2FtGrNMd6ngGjUURS0PQobZYKKuJR5ywS5qU; address=s%3Aundefined.H4tl815DCZ6%2Fo5v13eAn2NGFexz2evmgMlUcBAJMXS8; addressId=s%3Aundefined.H4tl815DCZ6%2Fo5v13eAn2NGFexz2evmgMlUcBAJMXS8; LocSrc=s%3AseoCty.Ln0AZvvgsCPuKj5IAqQw2NnSsBG0BSCZyoU1v9a5kXs; _gcl_au=1.1.767628066.1778994384; _fbp=fb.1.1778994384649.317500648794556559; _ga_8N8XRG907L=GS2.1.s1778994384$o1$g0$t1778994388$j56$l0$h0; _ga_VEG1HFE5VZ=GS2.1.s1778994384$o1$g0$t1778994388$j56$l0$h0; _ga_0XZC5MS97H=GS2.1.s1778994384$o1$g0$t1778994388$j56$l0$h0; __SW=4OMPPLCWeRY0OzFmn3vpzvtQcc0mYA_7; _device_id=e0d26997-bc41-907f-2511-625189e8e78e; _gid=GA1.2.1634202432.1778994395; _gat_0=1; fontsLoaded=1; _is_logged_in=1; _session_tid=f3e95fbf7453de1e5059a3146c16f1e5939c614cda7f6d5311e39dc8f0ba6b7fd4efb1933ccd480a13f22698191cfda6428307f7bc0abf88e83a6917901be6285436094dcfad96d3a71f0f68c8343547e611cbf0a5745e981d8e93db5e9cb2e033cccd61b925dea4f8b2872bcf647f5d41c6ae87a1e655f4dbe524e644de2506cd8083af33618eae0d75a6c997552cef3339836f5176e21712c3dd29ce93bcbc86605b9b1a5e599742f1c7a94d259cace544fcc8588c4e9ca8730c003adaab7f47ab7e8babf6d9f4660b952105a86952d72c98f83bf2e38bd3e266f18bd78ba5a6a02cfe3358fb9f8b005ebc561fd7e252173e504dfd087480a4ca403fac5a216937b039fcb267771f9426c3e028890213356b976c49ff314b759756dc25ce6a8ad2a9bd050350fd5cdc77d2657e43a2e99b1e1628008724c041505ec7ad57346d1989bbdc7ecb43699338cae746b8d0f8a21577a0639bdcedba843f3588f9a8688be21b5a24e2326bd7019d8eaf2780ea927385d5e6e3d66e4c1aa8a0e95db1626ab4865e6553610648a5742f5d9b8455a724e2c38f0d02d878a028a10eef9de68a4156d5df5a2bd73c6feef1a91c69b665130a2334f5532cb14a326b7fcde150ee75332119397ebada3d9764606c16aea7f46edd3f61fc770359421956cf4b9648149e6ca90795884415c393bcaa16fb70696e776bd113ed224faa449c45dc294197997442a0ce82b9c9ceafc7efc14bfa32735a74fbbf5ef5d1facb4f4ebf4a0b2a2d4bb9544d797f53337d3fd2f643228e8cbf32fdd1331f09fc6104d8317d471464fdee4da9b64ecd30be68423ea936f5716eab6c69ec10a58b121730557ef0c82aaf3479fd4b124cc9e1f889b1bc28f017abb0e2ac06aa61b50ad597234c4b5292eca0ac3f4e25d3632e2313ae0aa67f078ad5cb6ca5980ea9d578b9e91c35afd3e47e54baafb3c68eb06018120251d40f4eebe7372d396fda16cbda0563dda4ab6ec1603a882b8deb9a12e3f885ca53be1e828573268bd83106dd95e85e9f57e508a5b678190afec1331e6ba558c30c7bdddb245c4a08b05ff7b37193164134d91efde8748ba41db33088c62774d9334826ac6081fac051c984a7a5f08363fb30458b609ed68d0a68aee62e39975e1c16bee98aa5a124e4ab8689d0bf28e44ab58456a788b4098d1a2a3eaa26c8e171eed582f2cf83bcdfd361d76960; _sid=rea0ef1f921-3be7-44af-a52b-ad78474ce; adl=true; userLocation={%22lat%22:%2220.2352035%22%2C%22lng%22:%2285.8340168%22%2C%22address%22:%22Basisthanagar%2C%20Old%20Town%2C%20Bhubaneswar%2C%20Odisha%20751002%2C%20India%22%2C%22area%22:%22%22%2C%22showUserDefaultAddressHint%22:false}; _ga_YE38MFJRBZ=GS2.1.s1778994394$o1$g1$t1778994417$j37$l0$h0; _ga_34JYJ0BCRN=GS2.1.s1778994394$o1$g1$t1778994417$j37$l0$h0; _ga=GA1.2.1952361605.1778994384; aws-waf-token=96e584ef-cc66-4748-921f-7d27f0a42a6e:HgoAnZojmJEQAAAA:UpKzFTQYqMZjP4GFBX47rgzbCRJz74n5GrEvVposhW1VotYt5KIW4xeWbIWItWwFVb2VIMA9Qyu8/FLFheNxhEghwmf+zCjaPoJiwzjcjNy1pZKskEBAT7kr3Yxyh+7lSqB2i6RWmEsJyopTBym//LYBqBl9GqjoqjR95QoyBvU7VEGJ0kuZpAlpjX1HbNQpGkeiejnq3YRfuFkJ+WXbFjP5832DO0Nr8V3zk6xxeRwbDh5lV3UY6VRT5Fg="
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
