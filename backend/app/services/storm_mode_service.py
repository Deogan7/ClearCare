"""Storm Mode service — activation, deactivation, and appointment conversion logic."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from app.models.referral import Referral, ReferralStatus, AppointmentType
from app.models.storm_mode import (
    StormModeEvent, StormConversionLog, StormDriverNotification,
    StormTrigger, DriverNotificationStatus,
)

logger = logging.getLogger(__name__)

DEFAULT_WINDOW_HOURS = 48


async def get_current_storm_mode(db: AsyncSession) -> StormModeEvent | None:
    """Return the most recent active storm mode event, or None."""
    result = await db.execute(
        select(StormModeEvent)
        .where(StormModeEvent.is_active.is_(True))
        .order_by(desc(StormModeEvent.activated_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def activate_storm_mode(
    db: AsyncSession,
    trigger: StormTrigger,
    window_hours: int = DEFAULT_WINDOW_HOURS,
    activated_by: str | None = None,
) -> dict:
    """Activate Storm Mode and convert eligible in-person appointments to virtual."""
    existing = await get_current_storm_mode(db)
    if existing:
        return {
            "status": "already_active",
            "activated_at": existing.activated_at.isoformat(),
            "trigger": existing.trigger.value,
            "window_hours": existing.window_hours,
            "converted_count": existing.converted_count,
        }

    event = StormModeEvent(
        is_active=True,
        trigger=trigger,
        window_hours=window_hours,
        activated_by=activated_by,
    )
    db.add(event)
    await db.flush()

    converted = await _convert_eligible_appointments(db, event)

    event.converted_count = converted
    await db.commit()
    await db.refresh(event)

    logger.info(
        "Storm Mode ACTIVATED (%s) — %d appointment(s) converted to virtual within %dh window.",
        trigger.value,
        converted,
        window_hours,
    )

    return {
        "status": "activated",
        "trigger": trigger.value,
        "window_hours": window_hours,
        "converted_count": converted,
        "activated_at": event.activated_at.isoformat(),
        "event_id": str(event.id),
    }


async def deactivate_storm_mode(db: AsyncSession) -> dict:
    """Deactivate the current Storm Mode session."""
    event = await get_current_storm_mode(db)
    if not event:
        return {"status": "not_active"}

    event.is_active = False
    event.deactivated_at = datetime.utcnow()
    await db.commit()

    logger.info("Storm Mode DEACTIVATED.")
    return {
        "status": "deactivated",
        "was_active_since": event.activated_at.isoformat(),
        "converted_count": event.converted_count,
    }


async def get_storm_mode_status(db: AsyncSession) -> dict:
    """Return the current Storm Mode status for the frontend."""
    event = await get_current_storm_mode(db)
    if not event:
        return {
            "is_active": False,
            "trigger": None,
            "activated_at": None,
            "window_hours": None,
            "converted_count": 0,
            "event_id": None,
        }

    return {
        "is_active": True,
        "trigger": event.trigger.value,
        "activated_at": event.activated_at.isoformat(),
        "window_hours": event.window_hours,
        "converted_count": event.converted_count,
        "activated_by": event.activated_by,
        "event_id": str(event.id),
    }


async def get_convertible_count(db: AsyncSession, window_hours: int = DEFAULT_WINDOW_HOURS) -> int:
    """Count how many appointments would be converted if storm mode activates now."""
    referrals = await _get_eligible_referrals(db, window_hours)
    return len(referrals)


async def _get_eligible_referrals(
    db: AsyncSession, window_hours: int
) -> list[Referral]:
    """Find in-person, non-urgent appointments within the conversion window."""
    now = datetime.utcnow()
    window_end = now + timedelta(hours=window_hours)

    result = await db.execute(
        select(Referral).where(
            Referral.scheduled_date.isnot(None),
            Referral.scheduled_date >= now,
            Referral.scheduled_date <= window_end,
            Referral.appointment_type == AppointmentType.IN_PERSON,
            Referral.status.in_([
                ReferralStatus.APPOINTMENT_SCHEDULED,
                ReferralStatus.PATIENT_NOTIFIED,
            ]),
        )
    )
    return list(result.scalars().all())


async def _convert_eligible_appointments(
    db: AsyncSession, event: StormModeEvent
) -> int:
    """Convert all eligible in-person appointments to virtual and log each one."""
    referrals = await _get_eligible_referrals(db, event.window_hours)

    # Eagerly load patients for driver notifications
    for referral in referrals:
        if not referral.patient:
            await db.execute(
                select(Referral)
                .where(Referral.id == referral.id)
                .options(selectinload(Referral.patient))
            )

    for referral in referrals:
        prev_type = referral.appointment_type.value if referral.appointment_type else "in_person"
        referral.appointment_type = AppointmentType.VIRTUAL

        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        storm_note = f"[Storm Mode] Appointment converted from in-person to virtual care ({event.trigger.value} trigger)."
        existing = referral.notes or ""
        referral.notes = f"{existing}\n[{ts}] {storm_note}".strip()

        log_entry = StormConversionLog(
            storm_event_id=event.id,
            referral_id=referral.id,
            ticket_id=referral.ticket_id,
            previous_type=prev_type,
            new_type="virtual",
        )
        db.add(log_entry)

        # Generate driver notification for appointments that had rides scheduled
        if referral.ride_needed:
            patient = referral.patient
            patient_name = f"{patient.first_name} {patient.last_name}" if patient else "Patient"
            date_str = (
                referral.scheduled_date.strftime("%B %d at %I:%M %p")
                if referral.scheduled_date else "upcoming date"
            )
            message = (
                f"Clearwater Ridge Medical Clinic: The appointment for {patient_name} on "
                f"{date_str} has been converted to virtual care due to severe weather. "
                f"The ride is no longer needed. Thank you for volunteering!"
            )
            driver_notif = StormDriverNotification(
                storm_event_id=event.id,
                referral_id=referral.id,
                ticket_id=referral.ticket_id,
                driver_name="Volunteer Driver",
                patient_name=patient_name,
                message=message,
                status=DriverNotificationStatus.SENT,
            )
            db.add(driver_notif)

    await db.flush()
    return len(referrals)
