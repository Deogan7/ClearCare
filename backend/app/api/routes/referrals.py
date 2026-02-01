import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.referral import Referral, ReferralStatus
from app.models.user import User
from app.schemas.referral import ReferralCreate, ReferralResponse, ReferralUpdate
from app.services import referral_service, voice_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=list[ReferralResponse])
async def list_referrals(
    status: ReferralStatus | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all referral tickets, optionally filtered by status."""
    stmt = select(Referral)
    if status is not None:
        stmt = stmt.where(Referral.status == status)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=ReferralResponse, status_code=201)
async def create_referral(
    data: ReferralCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new referral ticket.

    In DEMO_MODE the first specialist verification call fires automatically
    within seconds of creation — no waiting for the scheduler.
    """
    referral = await referral_service.create_referral(db, data)

    if settings.DEMO_MODE and referral.specialist_phone:
        # Clear next_follow_up_at so the scheduler doesn't also pick this up
        # while we're already placing the call. The webhook will set the next one.
        referral.next_follow_up_at = None
        await db.commit()

        # Reload with patient relationship for the voice prompt
        refreshed = await referral_service.get_referral_by_ticket_id(db, referral.ticket_id)
        if refreshed:
            async def _fire_first_call(ref: Referral):
                """Background task: call specialist right after referral creation."""
                await asyncio.sleep(5)  # small delay so the API response returns first
                try:
                    result = await voice_service.call_specialist_verify_receipt(ref)
                    if result:
                        logger.info(
                            "Auto-call: Specialist verification call placed for %s",
                            ref.ticket_id,
                        )
                except Exception:
                    logger.exception(
                        "Auto-call: Failed specialist call for %s", ref.ticket_id
                    )

            asyncio.create_task(_fire_first_call(refreshed))

    return referral


@router.get("/{ticket_id}", response_model=ReferralResponse)
async def get_referral(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single referral by ticket ID."""
    referral = await referral_service.get_referral_by_ticket_id(db, ticket_id)
    if not referral:
        raise HTTPException(status_code=404, detail=f"Referral {ticket_id} not found")
    return referral


@router.patch("/{ticket_id}", response_model=ReferralResponse)
async def update_referral(
    ticket_id: str,
    data: ReferralUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update referral status or details."""
    referral = await referral_service.get_referral_by_ticket_id(db, ticket_id)
    if not referral:
        raise HTTPException(status_code=404, detail=f"Referral {ticket_id} not found")
    try:
        return await referral_service.update_referral(db, referral, data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
