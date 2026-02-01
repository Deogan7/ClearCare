"""Workflow engine — periodic task that drives the referral state machine.

Runs every 15 minutes and checks for referrals that need automated action:
1. 48h after referral sent → call specialist to verify receipt
2. 5 business days after resend → call specialist again
3. After referral received → call specialist to check appointment scheduling
4. After appointment scheduled → call patient with details
5. 1 business day after appointment → call patient for follow-up
"""

import logging

from app.db.session import async_session
from app.services import referral_service, voice_service

logger = logging.getLogger(__name__)


async def run_workflow_engine() -> None:
    """Main workflow loop — check all referral stages and trigger appropriate calls."""
    try:
        async with async_session() as db:
            await _process_specialist_verification_calls(db)
            await _process_appointment_check_calls(db)
            await _process_patient_notification_calls(db)
            await _process_post_appointment_followups(db)
    except Exception:
        logger.exception("Workflow engine failed")


async def _process_specialist_verification_calls(db) -> None:
    """Step 1 & 2: Call specialist offices to verify referral receipt."""
    referrals = await referral_service.get_referrals_needing_specialist_call(db)
    if not referrals:
        return

    logger.info("Workflow: %d referral(s) need specialist verification call.", len(referrals))

    for referral in referrals:
        try:
            result = await voice_service.call_specialist_verify_receipt(referral)
            if result:
                await referral_service.record_call_attempt(db, referral)
                logger.info(
                    "Workflow: Specialist verification call placed for %s (attempt #%d).",
                    referral.ticket_id,
                    referral.specialist_call_attempts,
                )
            else:
                logger.warning(
                    "Workflow: Could not call specialist for %s — no phone number.",
                    referral.ticket_id,
                )
                # Schedule retry in 24h so we don't spam logs
                await referral_service.schedule_next_follow_up(db, referral, hours=24)
        except Exception:
            logger.exception("Workflow: Failed specialist call for %s.", referral.ticket_id)


async def _process_appointment_check_calls(db) -> None:
    """Step 3: Call specialist offices to check if appointment is scheduled."""
    referrals = await referral_service.get_referrals_needing_appointment_check(db)
    if not referrals:
        return

    logger.info("Workflow: %d referral(s) need appointment scheduling check.", len(referrals))

    for referral in referrals:
        try:
            result = await voice_service.call_specialist_check_appointment(referral)
            if result:
                await referral_service.record_call_attempt(db, referral)
                logger.info("Workflow: Appointment check call placed for %s.", referral.ticket_id)
            else:
                logger.warning("Workflow: Could not call specialist for %s.", referral.ticket_id)
                await referral_service.schedule_next_follow_up(db, referral, hours=24)
        except Exception:
            logger.exception("Workflow: Failed appointment check call for %s.", referral.ticket_id)


async def _process_patient_notification_calls(db) -> None:
    """Step 4: Call patients to notify them about their scheduled appointment."""
    referrals = await referral_service.get_referrals_needing_patient_notification(db)
    if not referrals:
        return

    logger.info("Workflow: %d referral(s) need patient notification.", len(referrals))

    for referral in referrals:
        try:
            result = await voice_service.call_patient_appointment_notification(referral)
            if result:
                logger.info("Workflow: Patient notification call placed for %s.", referral.ticket_id)
            else:
                logger.warning("Workflow: Could not call patient for %s.", referral.ticket_id)
        except Exception:
            logger.exception("Workflow: Failed patient notification for %s.", referral.ticket_id)


async def _process_post_appointment_followups(db) -> None:
    """Step 5: Call patients after their appointment to check if they attended."""
    referrals = await referral_service.get_referrals_needing_post_appointment_followup(db)
    if not referrals:
        return

    logger.info("Workflow: %d referral(s) need post-appointment follow-up.", len(referrals))

    for referral in referrals:
        try:
            result = await voice_service.call_patient_post_appointment(referral)
            if result:
                logger.info("Workflow: Post-appointment call placed for %s.", referral.ticket_id)
            else:
                logger.warning("Workflow: Could not call patient for %s.", referral.ticket_id)
        except Exception:
            logger.exception("Workflow: Failed post-appointment call for %s.", referral.ticket_id)
