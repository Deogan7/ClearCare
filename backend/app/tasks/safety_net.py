"""Safety Net task — catches referrals that haven't been attended within the configured window.

Per the TRD: if a ticket is not marked as Attended within 48 hours of its scheduled date,
the system triggers a high-priority alert to the nurse and an automated follow-up call via Vapi.
"""

import logging

from app.db.session import async_session
from app.models.referral import ReferralStatus
from app.services.referral_service import get_overdue_referrals, transition_status
from app.services.voice_service import initiate_patient_follow_up_call

logger = logging.getLogger(__name__)


async def check_safety_net() -> None:
    """Scan for overdue referrals and trigger alerts + automated calls."""
    try:
        async with async_session() as db:
            overdue = await get_overdue_referrals(db)

            if not overdue:
                logger.debug("Safety net check: no overdue referrals.")
                return

            logger.warning("Safety net: %d overdue referral(s) found.", len(overdue))

            for referral in overdue:
                # Transition to MISSED so it shows up as a high-priority alert.
                try:
                    await transition_status(db, referral, ReferralStatus.MISSED)
                    logger.info(
                        "Referral %s marked as MISSED (was scheduled for %s).",
                        referral.ticket_id,
                        referral.scheduled_date,
                    )
                except ValueError:
                    # Already transitioned by another process.
                    pass

                # Trigger an automated Vapi follow-up call to the patient.
                await initiate_patient_follow_up_call(referral)

    except Exception:
        logger.exception("Safety net check failed")
