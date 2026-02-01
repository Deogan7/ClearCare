import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.referral import AppointmentType, ReferralStatus


class ReferralBase(BaseModel):
    patient_id: uuid.UUID
    description: str | None = None
    referred_to: str
    specialist_phone: str | None = None
    action_date: datetime
    scheduled_date: datetime | None = None
    notes: str | None = None


class ReferralCreate(ReferralBase):
    created_by: str


class ReferralUpdate(BaseModel):
    status: ReferralStatus | None = None
    scheduled_date: datetime | None = None
    specialist_phone: str | None = None
    appointment_type: AppointmentType | None = None
    ride_needed: bool | None = None
    ride_scheduled_time: datetime | None = None
    notes: str | None = None


class ReferralResponse(ReferralBase):
    id: uuid.UUID
    ticket_id: str
    status: ReferralStatus
    appointment_type: AppointmentType | None = None
    ride_needed: bool | None = None
    ride_scheduled_time: datetime | None = None
    specialist_call_attempts: int = 0
    last_call_at: datetime | None = None
    next_follow_up_at: datetime | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
