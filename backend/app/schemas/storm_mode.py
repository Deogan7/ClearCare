from pydantic import BaseModel


class StormModeActivateRequest(BaseModel):
    mode: str = "manual"
    window_hours: int = 48


class StormModeResponse(BaseModel):
    status: str
    trigger: str | None = None
    window_hours: int | None = None
    converted_count: int = 0
    activated_at: str | None = None
    was_active_since: str | None = None
    activated_by: str | None = None
    event_id: str | None = None


class StormModeStatusResponse(BaseModel):
    is_active: bool
    trigger: str | None = None
    activated_at: str | None = None
    window_hours: int | None = None
    converted_count: int = 0
    activated_by: str | None = None
    event_id: str | None = None


class ConvertibleCountResponse(BaseModel):
    count: int
    window_hours: int


# ---------------------------------------------------------------------------
# Wellness Check schemas
# ---------------------------------------------------------------------------

class WellnessCheckItem(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    status: str
    feeling_ok: bool | None = None
    has_symptoms: bool | None = None
    symptom_details: str | None = None
    medication_stocked: bool | None = None
    needs_assistance: bool | None = None
    assistance_details: str | None = None
    called_at: str | None = None
    completed_at: str | None = None


class WellnessCheckSummary(BaseModel):
    total: int
    pending: int = 0
    calling: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    checks: list[WellnessCheckItem] = []
    alerts: list[WellnessCheckItem] = []


# ---------------------------------------------------------------------------
# Driver Notification schemas
# ---------------------------------------------------------------------------

class DriverNotificationItem(BaseModel):
    id: str
    ticket_id: str
    driver_name: str | None = None
    patient_name: str
    message: str
    status: str
    created_at: str


class DriverNotificationSummary(BaseModel):
    total: int
    notifications: list[DriverNotificationItem] = []
