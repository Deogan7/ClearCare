from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.referral import Referral, ReferralStatus
from app.models.user import User
from app.schemas.referral import ReferralCreate, ReferralResponse, ReferralUpdate
from app.services import referral_service

router = APIRouter()


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
    """Create a new referral ticket."""
    return await referral_service.create_referral(db, data)


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
