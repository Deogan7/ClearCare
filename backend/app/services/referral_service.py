"""Core referral management logic — ticket creation, state transitions, safety net."""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.patient import Patient
from app.models.referral import Referral, ReferralStatus
from app.schemas.referral import ReferralCreate, ReferralUpdate


# Valid state transitions for the referral ticket state machine.
VALID_TRANSITIONS: dict[ReferralStatus, list[ReferralStatus]] = {
    ReferralStatus.PENDING_CONFIRMATION: [ReferralStatus.SCHEDULED, ReferralStatus.MISSED],
    ReferralStatus.SCHEDULED: [ReferralStatus.ATTENDED, ReferralStatus.MISSED],
    ReferralStatus.ATTENDED: [ReferralStatus.RESOLVED],
    ReferralStatus.RESOLVED: [],
    ReferralStatus.MISSED: [ReferralStatus.SCHEDULED],
}


def _generate_ticket_id() -> str:
    """Generate a short, human-readable ticket ID like RC-A1B2C3."""
    short = uuid.uuid4().hex[:6].upper()
    return f"RC-{short}"


async def create_referral(db: AsyncSession, data: ReferralCreate) -> Referral:
    """Create a new referral and assign it a unique ticket ID."""
    referral = Referral(
        ticket_id=_generate_ticket_id(),
        patient_id=data.patient_id,
        description=data.description,
        referred_to=data.referred_to,
        action_date=data.action_date,
        scheduled_date=data.scheduled_date,
        notes=data.notes,
        created_by=data.created_by,
        status=ReferralStatus.PENDING_CONFIRMATION,
    )
    db.add(referral)
    await db.commit()
    await db.refresh(referral)
    return referral


async def transition_status(
    db: AsyncSession, referral: Referral, new_status: ReferralStatus
) -> Referral:
    """Transition a referral to a new state, enforcing the state machine rules."""
    allowed = VALID_TRANSITIONS.get(referral.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition from {referral.status.value} to {new_status.value}. "
            f"Allowed transitions: {[s.value for s in allowed]}"
        )
    referral.status = new_status
    await db.commit()
    await db.refresh(referral)
    return referral


async def update_referral(
    db: AsyncSession, referral: Referral, data: ReferralUpdate
) -> Referral:
    """Update referral fields. Status changes go through the state machine."""
    if data.status is not None and data.status != referral.status:
        await transition_status(db, referral, data.status)
    if data.scheduled_date is not None:
        referral.scheduled_date = data.scheduled_date
    if data.notes is not None:
        referral.notes = data.notes
    await db.commit()
    await db.refresh(referral)
    return referral


async def get_referral_by_ticket_id(db: AsyncSession, ticket_id: str) -> Referral | None:
    result = await db.execute(select(Referral).where(Referral.ticket_id == ticket_id))
    return result.scalar_one_or_none()


async def get_overdue_referrals(db: AsyncSession) -> list[Referral]:
    """Find referrals in SCHEDULED state where the scheduled date + safety net window has passed."""
    cutoff = datetime.utcnow() - timedelta(hours=settings.SAFETY_NET_HOURS)
    result = await db.execute(
        select(Referral).where(
            Referral.status == ReferralStatus.SCHEDULED,
            Referral.scheduled_date <= cutoff,
        )
    )
    return list(result.scalars().all())


async def get_upcoming_referrals(db: AsyncSession, within_hours: int = 72) -> list[Referral]:
    """Get referrals with appointments scheduled within the next N hours."""
    now = datetime.utcnow()
    window = now + timedelta(hours=within_hours)
    result = await db.execute(
        select(Referral).where(
            Referral.status == ReferralStatus.SCHEDULED,
            Referral.scheduled_date >= now,
            Referral.scheduled_date <= window,
        )
    )
    return list(result.scalars().all())


async def get_high_risk_patients_with_upcoming(db: AsyncSession) -> list[dict]:
    """Get high-risk patients who have upcoming scheduled referrals."""
    result = await db.execute(
        select(Patient, Referral)
        .join(Referral, Patient.id == Referral.patient_id)
        .where(
            Patient.is_high_risk.is_(True),
            Referral.status == ReferralStatus.SCHEDULED,
            Referral.scheduled_date >= datetime.utcnow(),
        )
    )
    return [{"patient": row.Patient, "referral": row.Referral} for row in result.all()]
