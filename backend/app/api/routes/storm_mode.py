"""Storm Mode API — activate, deactivate, status, preview, wellness checks, driver notifications."""

import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db, async_session
from app.models.storm_mode import StormTrigger, StormDriverNotification
from app.models.user import User
from app.schemas.storm_mode import (
    StormModeActivateRequest,
    StormModeResponse,
    StormModeStatusResponse,
    ConvertibleCountResponse,
)
from app.core.config import settings
from app.services import storm_mode_service, storm_wellness_service

router = APIRouter()
logger = logging.getLogger(__name__)


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
    """Activate Storm Mode — converts appointments + triggers wellness checks."""
    trigger = StormTrigger.AUTO if data.mode == "auto" else StormTrigger.MANUAL
    result = await storm_mode_service.activate_storm_mode(
        db,
        trigger=trigger,
        window_hours=data.window_hours,
        activated_by=current_user.full_name,
    )

    # If freshly activated, trigger wellness checks for high-risk patients in background
    if result["status"] == "activated" and result.get("event_id"):
        event_id_str = result["event_id"]

        async def _fire_wellness_checks():
            delay = 5 if settings.DEMO_MODE else 3
            await asyncio.sleep(delay)  # small delay so the activation response returns first
            try:
                async with async_session() as wellness_db:
                    await storm_wellness_service.trigger_wellness_checks(
                        wellness_db, uuid.UUID(event_id_str)
                    )
            except Exception:
                logger.exception("Failed to trigger storm wellness checks")

        asyncio.create_task(_fire_wellness_checks())

    return result


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


@router.get("/wellness-checks")
async def get_wellness_checks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get wellness check progress for the current active storm event."""
    event = await storm_mode_service.get_current_storm_mode(db)
    if not event:
        return {"total": 0, "pending": 0, "calling": 0, "completed": 0, "failed": 0, "skipped": 0, "checks": [], "alerts": []}

    return await storm_wellness_service.get_wellness_check_summary(db, event.id)


@router.get("/driver-notifications")
async def get_driver_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get driver notification log for the current active storm event."""
    event = await storm_mode_service.get_current_storm_mode(db)
    if not event:
        return {"total": 0, "notifications": []}

    result = await db.execute(
        select(StormDriverNotification)
        .where(StormDriverNotification.storm_event_id == event.id)
        .order_by(StormDriverNotification.created_at.desc())
    )
    notifications = result.scalars().all()
    return {
        "total": len(list(notifications)),
        "notifications": [
            {
                "id": str(n.id),
                "ticket_id": n.ticket_id,
                "driver_name": n.driver_name,
                "patient_name": n.patient_name,
                "message": n.message,
                "status": n.status.value,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ],
    }
