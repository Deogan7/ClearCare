"""Core referral management logic — ticket creation, state transitions, workflow scheduling."""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.patient import Patient
from app.models.referral import Referral, ReferralStatus
from app.schemas.referral import ReferralCreate, ReferralUpdate


# ---------------------------------------------------------------------------
# Full workflow state machine
# ---------------------------------------------------------------------------
#
# SENT_TO_SPECIALIST  --(48h AI call)--> REFERRAL_RECEIVED | RESENT_TO_SPECIALIST
# RESENT_TO_SPECIALIST --(5 biz days)--> REFERRAL_RECEIVED | RESENT_TO_SPECIALIST (loop)
# REFERRAL_RECEIVED   --(AI call)------> APPOINTMENT_SCHEDULED | APPOINTMENT_SCHEDULING
# APPOINTMENT_SCHEDULING -(follow-up)---> APPOINTMENT_SCHEDULED
# APPOINTMENT_SCHEDULED -(AI call pt)---> PATIENT_NOTIFIED
# PATIENT_NOTIFIED    --(1 biz day)----> COMPLETED | MISSED
# MISSED              -(reschedule?)---> RESCHEDULE_REQUESTED | CLOSED
# RESCHEDULE_REQUESTED -(loop)---------> SENT_TO_SPECIALIST
# COMPLETED           -----------------> CLOSED
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[ReferralStatus, list[ReferralStatus]] = {
    ReferralStatus.SENT_TO_SPECIALIST: [
        ReferralStatus.REFERRAL_RECEIVED,
        ReferralStatus.RESENT_TO_SPECIALIST,
    ],
    ReferralStatus.RESENT_TO_SPECIALIST: [
        ReferralStatus.REFERRAL_RECEIVED,
        ReferralStatus.RESENT_TO_SPECIALIST,  # re-resend loop
    ],
    ReferralStatus.REFERRAL_RECEIVED: [
        ReferralStatus.APPOINTMENT_SCHEDULED,
        ReferralStatus.APPOINTMENT_SCHEDULING,
    ],
    ReferralStatus.APPOINTMENT_SCHEDULING: [
        ReferralStatus.APPOINTMENT_SCHEDULED,
    ],
    ReferralStatus.APPOINTMENT_SCHEDULED: [
        ReferralStatus.PATIENT_NOTIFIED,
    ],
    ReferralStatus.PATIENT_NOTIFIED: [
        ReferralStatus.COMPLETED,
        ReferralStatus.MISSED,
    ],
    ReferralStatus.COMPLETED: [
        ReferralStatus.CLOSED,
    ],
    ReferralStatus.MISSED: [
        ReferralStatus.RESCHEDULE_REQUESTED,
        ReferralStatus.CLOSED,
    ],
    ReferralStatus.RESCHEDULE_REQUESTED: [
        ReferralStatus.SENT_TO_SPECIALIST,  # loop back to start
    ],
    ReferralStatus.CLOSED: [],
}


def _generate_ticket_id() -> str:
    short = uuid.uuid4().hex[:6].upper()
    return f"RC-{short}"


def _add_business_days(start: datetime, days: int) -> datetime:
    """Add N business days (Mon-Fri) to a datetime."""
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

async def create_referral(db: AsyncSession, data: ReferralCreate) -> Referral:
    now = datetime.utcnow()
    referral = Referral(
        ticket_id=_generate_ticket_id(),
        patient_id=data.patient_id,
        description=data.description,
        referred_to=data.referred_to,
        specialist_phone=data.specialist_phone,
        action_date=data.action_date,
        scheduled_date=data.scheduled_date,
        notes=data.notes,
        created_by=data.created_by,
        status=ReferralStatus.SENT_TO_SPECIALIST,
        specialist_call_attempts=0,
        # First AI call to specialist 48h after creation
        next_follow_up_at=now + timedelta(hours=48),
    )
    db.add(referral)
    await db.commit()
    await db.refresh(referral)
    return referral


async def transition_status(
    db: AsyncSession, referral: Referral, new_status: ReferralStatus
) -> Referral:
    allowed = VALID_TRANSITIONS.get(referral.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition from {referral.status.value} to {new_status.value}. "
            f"Allowed: {[s.value for s in allowed]}"
        )
    referral.status = new_status
    await db.commit()
    await db.refresh(referral)
    return referral


async def update_referral(
    db: AsyncSession, referral: Referral, data: ReferralUpdate
) -> Referral:
    if data.status is not None and data.status != referral.status:
        await transition_status(db, referral, data.status)
    for field in ["scheduled_date", "specialist_phone", "appointment_type",
                   "ride_needed", "ride_scheduled_time", "notes"]:
        value = getattr(data, field, None)
        if value is not None:
            setattr(referral, field, value)
    await db.commit()
    await db.refresh(referral)
    return referral


async def get_referral_by_ticket_id(db: AsyncSession, ticket_id: str) -> Referral | None:
    result = await db.execute(
        select(Referral)
        .where(Referral.ticket_id == ticket_id)
        .options(selectinload(Referral.patient))
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Workflow queries (used by scheduler tasks)
# ---------------------------------------------------------------------------

async def get_referrals_needing_specialist_call(db: AsyncSession) -> list[Referral]:
    """Referrals in SENT or RESENT where next_follow_up_at has passed."""
    now = datetime.utcnow()
    result = await db.execute(
        select(Referral)
        .where(
            Referral.status.in_([
                ReferralStatus.SENT_TO_SPECIALIST,
                ReferralStatus.RESENT_TO_SPECIALIST,
            ]),
            Referral.next_follow_up_at <= now,
        )
        .options(selectinload(Referral.patient))
    )
    return list(result.scalars().all())


async def get_referrals_needing_appointment_check(db: AsyncSession) -> list[Referral]:
    """Referrals in REFERRAL_RECEIVED or APPOINTMENT_SCHEDULING where follow-up is due."""
    now = datetime.utcnow()
    result = await db.execute(
        select(Referral)
        .where(
            Referral.status.in_([
                ReferralStatus.REFERRAL_RECEIVED,
                ReferralStatus.APPOINTMENT_SCHEDULING,
            ]),
            Referral.next_follow_up_at <= now,
        )
        .options(selectinload(Referral.patient))
    )
    return list(result.scalars().all())


async def get_referrals_needing_patient_notification(db: AsyncSession) -> list[Referral]:
    """Referrals in APPOINTMENT_SCHEDULED that need to notify the patient."""
    result = await db.execute(
        select(Referral)
        .where(Referral.status == ReferralStatus.APPOINTMENT_SCHEDULED)
        .options(selectinload(Referral.patient))
    )
    return list(result.scalars().all())


async def get_referrals_needing_post_appointment_followup(db: AsyncSession) -> list[Referral]:
    """Referrals in PATIENT_NOTIFIED where post-appointment follow-up is due."""
    now = datetime.utcnow()
    result = await db.execute(
        select(Referral)
        .where(
            Referral.status == ReferralStatus.PATIENT_NOTIFIED,
            Referral.next_follow_up_at <= now,
        )
        .options(selectinload(Referral.patient))
    )
    return list(result.scalars().all())


async def record_call_attempt(db: AsyncSession, referral: Referral) -> None:
    referral.specialist_call_attempts += 1
    referral.last_call_at = datetime.utcnow()
    await db.commit()


async def schedule_next_follow_up(
    db: AsyncSession, referral: Referral, business_days: int = 0, hours: int = 0
) -> None:
    now = datetime.utcnow()
    if business_days > 0:
        referral.next_follow_up_at = _add_business_days(now, business_days)
    elif hours > 0:
        referral.next_follow_up_at = now + timedelta(hours=hours)
    else:
        referral.next_follow_up_at = None
    await db.commit()


async def get_overdue_referrals(db: AsyncSession) -> list[Referral]:
    cutoff = datetime.utcnow() - timedelta(hours=settings.SAFETY_NET_HOURS)
    result = await db.execute(
        select(Referral).where(
            Referral.status == ReferralStatus.APPOINTMENT_SCHEDULED,
            Referral.scheduled_date <= cutoff,
        )
    )
    return list(result.scalars().all())


async def get_upcoming_referrals(db: AsyncSession, within_hours: int = 72) -> list[Referral]:
    now = datetime.utcnow()
    window = now + timedelta(hours=within_hours)
    result = await db.execute(
        select(Referral).where(
            Referral.status == ReferralStatus.APPOINTMENT_SCHEDULED,
            Referral.scheduled_date >= now,
            Referral.scheduled_date <= window,
        )
    )
    return list(result.scalars().all())


async def get_high_risk_patients_with_upcoming(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Patient, Referral)
        .join(Referral, Patient.id == Referral.patient_id)
        .where(
            Patient.is_high_risk.is_(True),
            Referral.status == ReferralStatus.APPOINTMENT_SCHEDULED,
            Referral.scheduled_date >= datetime.utcnow(),
        )
    )
    return [{"patient": row.Patient, "referral": row.Referral} for row in result.all()]
