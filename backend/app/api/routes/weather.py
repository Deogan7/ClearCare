from fastapi import APIRouter

router = APIRouter()


@router.get("/current")
async def get_current_weather():
    """Fetch current weather conditions for the configured location."""
    pass


@router.get("/storm-status")
async def get_storm_status():
    """Check whether Storm Mode thresholds are currently met."""
    pass
