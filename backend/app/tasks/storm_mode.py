"""Storm Mode — activated when severe weather thresholds are exceeded.

Actions:
  1. Auto-convert upcoming in-person appointments to virtual care.
"""

import logging

from app.db.session import async_session
from app.models.storm_mode import StormTrigger
from app.services import storm_mode_service
from app.services.weather_service import WeatherCondition

logger = logging.getLogger(__name__)


async def activate_storm_mode(condition: WeatherCondition) -> None:
    """Auto-activate Storm Mode when severe weather is detected by the poller."""
    logger.warning("STORM MODE AUTO-TRIGGER — %s", condition.description)

    async with async_session() as db:
        result = await storm_mode_service.activate_storm_mode(
            db,
            trigger=StormTrigger.AUTO,
            window_hours=48,
            activated_by="Weather Auto-Trigger",
        )

    if result["status"] == "already_active":
        logger.info("Storm Mode already active — skipping.")
    else:
        logger.warning(
            "Storm Mode ACTIVATED (auto): %d appointment(s) converted.",
            result.get("converted_count", 0),
        )
