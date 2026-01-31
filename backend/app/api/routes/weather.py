from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.models.user import User
from app.core.config import settings
from app.services.weather_service import check_weather_alerts, fetch_current_weather

router = APIRouter()


@router.get("/current")
async def get_current_weather(current_user: User = Depends(get_current_user)):
    """Fetch current weather conditions for the configured location."""
    try:
        condition = await fetch_current_weather()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Weather service unavailable") from exc

    return {
        "temperature_c": condition.temperature_c,
        "snow_cm": condition.snow_cm,
        "description": condition.description,
        "is_severe": condition.is_severe,
        "thresholds": {
            "snow_cm": settings.SNOW_THRESHOLD_CM,
            "temp_c": settings.TEMP_THRESHOLD_C,
        },
        "location": {
            "lat": settings.WEATHER_LOCATION_LAT,
            "lon": settings.WEATHER_LOCATION_LON,
        },
    }


@router.get("/storm-status")
async def get_storm_status(current_user: User = Depends(get_current_user)):
    """Check whether Storm Mode thresholds are currently met."""
    try:
        condition = await fetch_current_weather()
        alerts = await check_weather_alerts()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Weather service unavailable") from exc

    return {
        "is_severe": condition.is_severe,
        "temperature_c": condition.temperature_c,
        "snow_cm": condition.snow_cm,
        "description": condition.description,
        "thresholds": {
            "snow_cm": settings.SNOW_THRESHOLD_CM,
            "temp_c": settings.TEMP_THRESHOLD_C,
        },
        "alerts": alerts,
    }
