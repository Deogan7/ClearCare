import uuid
from datetime import datetime

from pydantic import BaseModel


class PatientBase(BaseModel):
    first_name: str
    last_name: str
    phone: str
    date_of_birth: datetime | None = None
    is_high_risk: bool = False
    address: str | None = None
    notes: str | None = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    date_of_birth: datetime | None = None
    is_high_risk: bool | None = None
    address: str | None = None
    notes: str | None = None


class PatientResponse(PatientBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
