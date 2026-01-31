import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.referral import ReferralStatus


class ReferralBase(BaseModel):
    patient_id: uuid.UUID
    description: str | None = None
    referred_to: str
    action_date: datetime
    scheduled_date: datetime | None = None
    notes: str | None = None


class ReferralCreate(ReferralBase):
    created_by: str


class ReferralUpdate(BaseModel):
    status: ReferralStatus | None = None
    scheduled_date: datetime | None = None
    notes: str | None = None


class ReferralResponse(ReferralBase):
    id: uuid.UUID
    ticket_id: str
    status: ReferralStatus
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
