import uuid

from pydantic import BaseModel


class FacilityResponse(BaseModel):
    id: uuid.UUID
    facility_name: str
    source_facility_type: str | None = None
    odhf_facility_type: str | None = None
    provider: str | None = None
    street_no: str | None = None
    street_name: str | None = None
    postal_code: str | None = None
    city: str | None = None
    province: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    model_config = {"from_attributes": True}
