import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.appointment import AppointmentStatus, RiskLevel


class AppointmentBase(BaseModel):
    patient_id: uuid.UUID
    title: str
    description: str | None = None
    risk_level: RiskLevel = RiskLevel.LOW
    appointment_date: datetime
    duration_minutes: int = 30
    provider: str
    location: str | None = None
    notes: str | None = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    risk_level: RiskLevel | None = None
    appointment_date: datetime | None = None
    duration_minutes: int | None = None
    provider: str | None = None
    status: AppointmentStatus | None = None
    location: str | None = None
    notes: str | None = None


class AppointmentResponse(AppointmentBase):
    id: uuid.UUID
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
