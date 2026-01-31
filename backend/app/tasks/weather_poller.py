"""Periodic weather polling task.

Fetches current weather conditions and triggers Storm Mode when thresholds are exceeded.
"""

import logging

from app.services.weather_service import fetch_current_weather
from app.tasks.storm_mode import activate_storm_mode

logger = logging.getLogger(__name__)


async def poll_weather() -> None:
    """Fetch current weather and trigger storm mode if conditions are severe."""
    try:
        condition = await fetch_current_weather()
        logger.info(
            "Weather check: %.1f°C, %.1fcm snow — %s",
            condition.temperature_c,
            condition.snow_cm,
            condition.description,
        )

        if condition.is_severe:
            logger.warning(
                "Severe weather detected (%.1f°C / %.1fcm snow). Activating Storm Mode.",
                condition.temperature_c,
                condition.snow_cm,
            )
            await activate_storm_mode(condition)
    except Exception:
        logger.exception("Weather polling failed")
