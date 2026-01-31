from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/current")
async def get_current_weather(current_user: User = Depends(get_current_user)):
    """Fetch current weather conditions for the configured location."""
    pass


@router.get("/storm-status")
async def get_storm_status(current_user: User = Depends(get_current_user)):
    """Check whether Storm Mode thresholds are currently met."""
    pass
