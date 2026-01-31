"""WeatherAPI polling and Storm Mode trigger logic."""

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


def _build_location_query() -> str:
    return f"{settings.WEATHER_LOCATION_LAT},{settings.WEATHER_LOCATION_LON}"


async def fetch_current_weather() -> WeatherCondition:
    """Poll WeatherAPI for current conditions at the configured location."""
    url = f"{settings.WEATHER_API_BASE_URL}/current.json"
    params = {
        "key": settings.WEATHER_API_KEY,
        "q": _build_location_query(),
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    current = data.get("current", {})
    temp_c = current.get("temp_c", 0.0)
    # WeatherAPI returns snowfall in cm.
    snow_cm = current.get("snow_cm", 0.0)
    condition = current.get("condition", {}) or {}
    description = condition.get("text", "")

    is_severe = snow_cm >= settings.SNOW_THRESHOLD_CM or temp_c <= settings.TEMP_THRESHOLD_C

    return WeatherCondition(
        temperature_c=temp_c,
        snow_cm=snow_cm,
        description=description,
        is_severe=is_severe,
    )


async def check_weather_alerts() -> list[dict]:
    """Fetch active weather alerts from WeatherAPI."""
    url = f"{settings.WEATHER_API_BASE_URL}/forecast.json"
    params = {
        "key": settings.WEATHER_API_KEY,
        "q": _build_location_query(),
        "days": 1,
        "alerts": "yes",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    alerts = data.get("alerts", {}) or {}
    return alerts.get("alert", [])
