from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


@router.get("/")
async def list_referrals(db: AsyncSession = Depends(get_db)):
    """List all active referral tickets."""
    pass


@router.post("/")
async def create_referral(db: AsyncSession = Depends(get_db)):
    """Create a new referral ticket."""
    pass


@router.get("/{ticket_id}")
async def get_referral(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single referral by ticket ID."""
    pass


@router.patch("/{ticket_id}")
async def update_referral(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """Update referral status or details."""
    pass
