import uuid
from datetime import datetime, timedelta
import random

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.appointment import Appointment, AppointmentStatus, RiskLevel
from app.models.patient import Patient
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
)

router = APIRouter()


@router.get("/", response_model=list[AppointmentResponse])
async def list_appointments(
    status: AppointmentStatus | None = Query(default=None),
    risk_level: RiskLevel | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all local appointments, optionally filtered by status or risk level."""
    stmt = select(Appointment).order_by(Appointment.appointment_date.asc())
    if status is not None:
        stmt = stmt.where(Appointment.status == status)
    if risk_level is not None:
        stmt = stmt.where(Appointment.risk_level == risk_level)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=AppointmentResponse, status_code=201)
async def create_appointment(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new local appointment."""
    appointment = Appointment(**data.model_dump())
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: uuid.UUID,
    data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)
    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.delete("/{appointment_id}", status_code=204)
async def delete_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    await db.delete(appointment)
    await db.commit()


@router.post("/seed", response_model=list[AppointmentResponse], status_code=201)
async def seed_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seed demo appointment data using existing patients."""
    result = await db.execute(select(Patient))
    patients = result.scalars().all()
    if not patients:
        raise HTTPException(
            status_code=400, detail="No patients found. Create patients first."
        )

    # Check if appointments already exist
    count_result = await db.execute(select(sa_func.count(Appointment.id)))
    existing_count = count_result.scalar() or 0
    if existing_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Appointments already seeded ({existing_count} exist). Delete them first to re-seed.",
        )

    providers = [
        "Dr. Sarah Chen",
        "Dr. James Wilson",
        "Dr. Maria Rodriguez",
        "Dr. Kevin Park",
        "NP Lisa Thompson",
    ]
    locations = [
        "Room 101",
        "Room 204",
        "Room 110",
        "Lab A",
        "Room 305",
        "Clinic B",
        "Room 102",
    ]
    appointment_templates = [
        {
            "title": "Annual Physical",
            "description": "Routine annual physical examination and wellness check.",
            "risk": RiskLevel.LOW,
            "duration": 45,
        },
        {
            "title": "Diabetes Follow-up",
            "description": "Blood sugar monitoring and insulin adjustment consultation.",
            "risk": RiskLevel.HIGH,
            "duration": 30,
        },
        {
            "title": "Blood Pressure Check",
            "description": "Hypertension monitoring, medication review.",
            "risk": RiskLevel.MODERATE,
            "duration": 20,
        },
        {
            "title": "Post-Surgery Review",
            "description": "Follow-up evaluation after recent knee replacement surgery.",
            "risk": RiskLevel.CRITICAL,
            "duration": 40,
        },
        {
            "title": "Lab Work - CBC",
            "description": "Complete blood count panel and metabolic screening.",
            "risk": RiskLevel.LOW,
            "duration": 15,
        },
        {
            "title": "Cardiac Assessment",
            "description": "Echocardiogram follow-up for arrhythmia monitoring.",
            "risk": RiskLevel.CRITICAL,
            "duration": 60,
        },
        {
            "title": "Medication Review",
            "description": "Quarterly review of current medication regimen and interactions.",
            "risk": RiskLevel.MODERATE,
            "duration": 25,
        },
        {
            "title": "Wound Care",
            "description": "Dressing change and wound assessment for diabetic ulcer.",
            "risk": RiskLevel.HIGH,
            "duration": 30,
        },
        {
            "title": "Mental Health Check-in",
            "description": "Routine mental health screening and wellbeing assessment.",
            "risk": RiskLevel.MODERATE,
            "duration": 30,
        },
        {
            "title": "Flu Vaccination",
            "description": "Seasonal influenza vaccination.",
            "risk": RiskLevel.LOW,
            "duration": 10,
        },
        {
            "title": "Respiratory Follow-up",
            "description": "COPD management review and spirometry test.",
            "risk": RiskLevel.HIGH,
            "duration": 35,
        },
        {
            "title": "Fall Risk Assessment",
            "description": "Balance testing and fall prevention evaluation.",
            "risk": RiskLevel.HIGH,
            "duration": 40,
        },
        {
            "title": "Nutrition Counseling",
            "description": "Dietary plan review for weight management program.",
            "risk": RiskLevel.LOW,
            "duration": 30,
        },
        {
            "title": "Physical Therapy Consult",
            "description": "Initial evaluation for chronic lower back pain treatment plan.",
            "risk": RiskLevel.MODERATE,
            "duration": 45,
        },
        {
            "title": "Eye Exam Referral Prep",
            "description": "Pre-referral assessment for diabetic retinopathy screening.",
            "risk": RiskLevel.HIGH,
            "duration": 20,
        },
    ]

    statuses = [
        AppointmentStatus.SCHEDULED,
        AppointmentStatus.SCHEDULED,
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.NO_SHOW,
        AppointmentStatus.CANCELLED,
    ]

    now = datetime.utcnow()
    created = []

    for i, template in enumerate(appointment_templates):
        patient = patients[i % len(patients)]

        # Spread across past few days and next two weeks
        day_offset = random.randint(-3, 14)
        hour = random.choice([8, 9, 10, 11, 13, 14, 15, 16])
        minute = random.choice([0, 15, 30, 45])
        appt_date = (now + timedelta(days=day_offset)).replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )

        # Past appointments get completed/no-show status, future get scheduled/confirmed
        if day_offset < 0:
            status = random.choice(
                [
                    AppointmentStatus.COMPLETED,
                    AppointmentStatus.COMPLETED,
                    AppointmentStatus.NO_SHOW,
                ]
            )
        elif day_offset == 0:
            status = random.choice(
                [
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.CHECKED_IN,
                    AppointmentStatus.IN_PROGRESS,
                ]
            )
        else:
            status = random.choice(
                [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]
            )

        appointment = Appointment(
            patient_id=patient.id,
            title=template["title"],
            description=template["description"],
            risk_level=template["risk"],
            appointment_date=appt_date,
            duration_minutes=template["duration"],
            provider=random.choice(providers),
            status=status,
            location=random.choice(locations),
        )
        db.add(appointment)
        created.append(appointment)

    await db.commit()
    for appt in created:
        await db.refresh(appt)

    return created
