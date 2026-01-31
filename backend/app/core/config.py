from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "RidgeCare Link"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ridgecare"

    # Vapi AI
    VAPI_API_KEY: str = ""
    VAPI_BASE_URL: str = "https://api.vapi.ai"

    # Twilio
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # Weather API
    WEATHER_API_KEY: str = ""
    WEATHER_API_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    WEATHER_LOCATION_LAT: float = 51.0447  # Default: Calgary area
    WEATHER_LOCATION_LON: float = -114.0719

    # Storm Mode thresholds
    SNOW_THRESHOLD_CM: float = 15.0
    TEMP_THRESHOLD_C: float = -35.0

    # Safety net
    SAFETY_NET_HOURS: int = 48

    # Auth
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hour shift
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
