from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


@router.get("/")
async def list_patients(db: AsyncSession = Depends(get_db)):
    pass


@router.post("/")
async def create_patient(db: AsyncSession = Depends(get_db)):
    pass


@router.get("/{patient_id}")
async def get_patient(patient_id: str, db: AsyncSession = Depends(get_db)):
    pass
