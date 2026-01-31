"""Storm Mode — activated when severe weather thresholds are exceeded.

Actions:
  1. Send SMS check-ins to all high-risk seniors.
  2. Initiate Vapi voice calls to reschedule upcoming physical visits into virtual care.
"""

import logging

from app.db.session import async_session
from app.services.referral_service import get_high_risk_patients_with_upcoming
from app.services.sms_service import send_storm_checkin_sms
from app.services.voice_service import initiate_reschedule_call
from app.services.weather_service import WeatherCondition

logger = logging.getLogger(__name__)


async def activate_storm_mode(condition: WeatherCondition) -> None:
    """Run all Storm Mode actions for a severe weather event."""
    logger.warning("STORM MODE ACTIVE — %s", condition.description)

    async with async_session() as db:
        records = await get_high_risk_patients_with_upcoming(db)

    # 1. SMS check-ins for high-risk patients.
    for record in records:
        patient = record["patient"]
        try:
            await send_storm_checkin_sms(patient, condition)
            logger.info("Storm SMS sent to patient %s %s.", patient.first_name, patient.last_name)
        except Exception:
            logger.exception("Failed to send storm SMS to patient %s.", patient.id)

    # 2. Voice calls to reschedule physical visits.
    for record in records:
        patient = record["patient"]
        referral = record["referral"]
        try:
            await initiate_reschedule_call(patient, referral, condition)
            logger.info(
                "Reschedule call initiated for referral %s (patient %s).",
                referral.ticket_id,
                patient.id,
            )
        except Exception:
            logger.exception(
                "Failed to initiate reschedule call for referral %s.", referral.ticket_id
            )
