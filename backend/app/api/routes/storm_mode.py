"""Storm Mode API — activate, deactivate, status, preview."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.storm_mode import StormTrigger
from app.models.user import User
from app.schemas.storm_mode import (
    StormModeActivateRequest,
    StormModeResponse,
    StormModeStatusResponse,
    ConvertibleCountResponse,
)
from app.services import storm_mode_service

router = APIRouter()


@router.get("/status", response_model=StormModeStatusResponse)
async def storm_mode_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current Storm Mode activation status."""
    return await storm_mode_service.get_storm_mode_status(db)


@router.post("/activate", response_model=StormModeResponse)
async def activate_storm_mode(
    data: StormModeActivateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate Storm Mode — converts eligible in-person appointments to virtual."""
    trigger = StormTrigger.AUTO if data.mode == "auto" else StormTrigger.MANUAL
    return await storm_mode_service.activate_storm_mode(
        db,
        trigger=trigger,
        window_hours=data.window_hours,
        activated_by=current_user.full_name,
    )


@router.post("/deactivate", response_model=StormModeResponse)
async def deactivate_storm_mode(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deactivate Storm Mode."""
    return await storm_mode_service.deactivate_storm_mode(db)


@router.get("/preview", response_model=ConvertibleCountResponse)
async def preview_conversions(
    window_hours: int = 48,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview how many appointments would be converted."""
    count = await storm_mode_service.get_convertible_count(db, window_hours)
    return {"count": count, "window_hours": window_hours}
