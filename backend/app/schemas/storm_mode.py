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


class StormModeStatusResponse(BaseModel):
    is_active: bool
    trigger: str | None = None
    activated_at: str | None = None
    window_hours: int | None = None
    converted_count: int = 0
    activated_by: str | None = None


class ConvertibleCountResponse(BaseModel):
    count: int
    window_hours: int
