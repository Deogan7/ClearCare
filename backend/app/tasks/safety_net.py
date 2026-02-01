"""Safety Net task — catches referrals that have been in PATIENT_NOTIFIED
but the appointment date is far past, indicating they may have been missed.

If the workflow engine hasn't already triggered a post-appointment call,
the safety net acts as a fallback to ensure no referral slips through.
"""

import logging

from app.db.session import async_session
from app.services.referral_service import get_overdue_referrals
from app.services.voice_service import call_patient_post_appointment

logger = logging.getLogger(__name__)


async def check_safety_net() -> None:
    """Scan for overdue referrals and trigger follow-up calls."""
    try:
        async with async_session() as db:
            overdue = await get_overdue_referrals(db)

            if not overdue:
                logger.debug("Safety net check: no overdue referrals.")
                return

            logger.warning("Safety net: %d overdue referral(s) found.", len(overdue))

            for referral in overdue:
                logger.info(
                    "Safety net: referral %s overdue (scheduled for %s). Triggering follow-up.",
                    referral.ticket_id,
                    referral.scheduled_date,
                )
                try:
                    await call_patient_post_appointment(referral)
                except Exception:
                    logger.exception(
                        "Safety net: failed to call patient for referral %s.",
                        referral.ticket_id,
                    )

    except Exception:
        logger.exception("Safety net check failed")
