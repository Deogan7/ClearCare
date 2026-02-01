from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.facility import Facility
from app.models.user import User
from app.schemas.facility import FacilityResponse

router = APIRouter()


@router.get("/search", response_model=list[FacilityResponse])
async def search_facilities(
    q: str = Query(..., min_length=2, description="Search by facility name, city, or postal code"),
    province: str | None = Query(default=None, description="Filter by province code (e.g. 'ab')"),
    facility_type: str | None = Query(default=None, description="Filter by ODHF facility type"),
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search facilities by name, city, or postal code."""
    search = f"%{q.lower()}%"
    stmt = (
        select(Facility)
        .where(
            func.lower(Facility.facility_name).like(search)
            | func.lower(Facility.city).like(search)
            | func.lower(Facility.postal_code).like(search)
        )
    )
    if province:
        stmt = stmt.where(func.lower(Facility.province) == province.lower())
    if facility_type:
        stmt = stmt.where(func.lower(Facility.odhf_facility_type).like(f"%{facility_type.lower()}%"))

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/types", response_model=list[str])
async def list_facility_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all distinct ODHF facility types in the database."""
    result = await db.execute(
        select(Facility.odhf_facility_type)
        .where(Facility.odhf_facility_type.isnot(None))
        .distinct()
        .order_by(Facility.odhf_facility_type)
    )
    return [row[0] for row in result.all()]


@router.get("/count")
async def facility_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get total number of facilities in the database."""
    result = await db.execute(select(func.count(Facility.id)))
    return {"count": result.scalar()}
