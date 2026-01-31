import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientResponse

router = APIRouter()


@router.get("/", response_model=list[PatientResponse])
async def list_patients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patient))
    return result.scalars().all()


@router.post("/", response_model=PatientResponse, status_code=201)
async def create_patient(data: PatientCreate, db: AsyncSession = Depends(get_db)):
    patient = Patient(**data.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
