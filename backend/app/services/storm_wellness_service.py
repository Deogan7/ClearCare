"""Storm Wellness Service — triggers and tracks wellness check calls for high-risk patients."""

import asyncio
import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.patient import Patient
from app.models.storm_mode import StormWellnessCheck, WellnessCheckStatus
from app.services import voice_service

logger = logging.getLogger(__name__)


async def trigger_wellness_checks(db: AsyncSession, storm_event_id: uuid.UUID) -> dict:
    """Query all high-risk patients and initiate wellness check calls.

    Creates a StormWellnessCheck record for each patient, then fires Vapi calls
    with a small stagger to avoid rate limits.

    In DEMO_MODE only one real call is placed (to STORM_DEMO_PHONE) so the
    presenter can take the live call on stage.  The remaining patients are
    marked as "calling" so the UI looks fully active.
    """
    result = await db.execute(
        select(Patient).where(Patient.is_high_risk.is_(True))
    )
    high_risk_patients = list(result.scalars().all())

    if not high_risk_patients:
        logger.info("No high-risk patients found for wellness checks.")
        return {"total": 0, "calling": 0, "skipped": 0}

    calling = 0
    skipped = 0
    demo_call_placed = False

    for patient in high_risk_patients:
        check = StormWellnessCheck(
            storm_event_id=storm_event_id,
            patient_id=patient.id,
            status=WellnessCheckStatus.PENDING,
        )
        db.add(check)
        await db.flush()

        if not patient.phone:
            check.status = WellnessCheckStatus.SKIPPED
            skipped += 1
            continue

        # ---- DEMO MODE: one real call to presenter's phone, rest are visual ----
        if settings.DEMO_MODE:
            if not demo_call_placed:
                try:
                    call_result = await voice_service.call_patient_wellness_check(
                        patient, storm_event_id,
                        phone_override=settings.STORM_DEMO_PHONE,
                    )
                    if call_result:
                        check.status = WellnessCheckStatus.CALLING
                        check.vapi_call_id = call_result.get("id")
                        check.called_at = datetime.utcnow()
                        calling += 1
                        demo_call_placed = True
                    else:
                        check.status = WellnessCheckStatus.FAILED
                except Exception:
                    logger.exception("DEMO: Failed wellness call for patient %s", patient.id)
                    check.status = WellnessCheckStatus.FAILED
            else:
                # Mark remaining patients as "calling" for demo UI appearance
                check.status = WellnessCheckStatus.CALLING
                check.called_at = datetime.utcnow()
                calling += 1
            await db.commit()
            continue

        # ---- PRODUCTION: call every patient ----
        try:
            call_result = await voice_service.call_patient_wellness_check(
                patient, storm_event_id
            )
            if call_result:
                check.status = WellnessCheckStatus.CALLING
                check.vapi_call_id = call_result.get("id")
                check.called_at = datetime.utcnow()
                calling += 1
            else:
                check.status = WellnessCheckStatus.FAILED
        except Exception:
            logger.exception("Failed to place wellness call for patient %s", patient.id)
            check.status = WellnessCheckStatus.FAILED

        await db.commit()

        # Small stagger between calls to avoid Vapi rate limits
        await asyncio.sleep(2)

    await db.commit()

    total = len(high_risk_patients)
    logger.info(
        "Storm wellness checks initiated: %d total, %d calling, %d skipped",
        total, calling, skipped,
    )
    return {"total": total, "calling": calling, "skipped": skipped}


async def get_wellness_check_summary(db: AsyncSession, storm_event_id: uuid.UUID) -> dict:
    """Return aggregated wellness check stats for the frontend."""
    result = await db.execute(
        select(StormWellnessCheck)
        .where(StormWellnessCheck.storm_event_id == storm_event_id)
        .options(selectinload(StormWellnessCheck.patient))
    )
    checks = list(result.scalars().all())

    status_counts = {
        "pending": 0,
        "calling": 0,
        "completed": 0,
        "failed": 0,
        "skipped": 0,
    }
    check_items = []
    alerts = []

    for wc in checks:
        status_counts[wc.status.value] = status_counts.get(wc.status.value, 0) + 1

        patient = wc.patient
        patient_name = f"{patient.first_name} {patient.last_name}" if patient else "Unknown"

        item = {
            "id": str(wc.id),
            "patient_id": str(wc.patient_id),
            "patient_name": patient_name,
            "status": wc.status.value,
            "feeling_ok": wc.feeling_ok,
            "has_symptoms": wc.has_symptoms,
            "symptom_details": wc.symptom_details,
            "medication_stocked": wc.medication_stocked,
            "needs_assistance": wc.needs_assistance,
            "assistance_details": wc.assistance_details,
            "called_at": wc.called_at.isoformat() if wc.called_at else None,
            "completed_at": wc.completed_at.isoformat() if wc.completed_at else None,
        }
        check_items.append(item)

        # Flag as alert if symptoms, low meds, or needs help
        if wc.status == WellnessCheckStatus.COMPLETED and (
            wc.has_symptoms or wc.medication_stocked is False or wc.needs_assistance
        ):
            alerts.append(item)

    return {
        "total": len(checks),
        **status_counts,
        "checks": check_items,
        "alerts": alerts,
    }
