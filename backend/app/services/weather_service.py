"""OpenWeatherMap polling and Storm Mode trigger logic."""

import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class WeatherCondition:
    temperature_c: float
    snow_cm: float
    description: str
    is_severe: bool


async def fetch_current_weather() -> WeatherCondition:
    """Poll OpenWeatherMap for current conditions at the configured location."""
    url = f"{settings.WEATHER_API_BASE_URL}/weather"
    params = {
        "lat": settings.WEATHER_LOCATION_LAT,
        "lon": settings.WEATHER_LOCATION_LON,
        "appid": settings.WEATHER_API_KEY,
        "units": "metric",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    temp_c = data["main"]["temp"]
    # Snow volume in last 3h (mm), convert to cm. Field may be absent.
    snow_mm = data.get("snow", {}).get("3h", 0.0)
    snow_cm = snow_mm / 10.0
    description = data["weather"][0]["description"] if data.get("weather") else ""

    is_severe = snow_cm >= settings.SNOW_THRESHOLD_CM or temp_c <= settings.TEMP_THRESHOLD_C

    return WeatherCondition(
        temperature_c=temp_c,
        snow_cm=snow_cm,
        description=description,
        is_severe=is_severe,
    )


async def check_weather_alerts() -> list[dict]:
    """Fetch active weather alerts from the One Call API endpoint."""
    url = f"{settings.WEATHER_API_BASE_URL}/onecall"
    params = {
        "lat": settings.WEATHER_LOCATION_LAT,
        "lon": settings.WEATHER_LOCATION_LON,
        "appid": settings.WEATHER_API_KEY,
        "exclude": "minutely,hourly,daily",
        "units": "metric",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    return data.get("alerts", [])
