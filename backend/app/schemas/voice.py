from pydantic import BaseModel


class VerifyReferralRequest(BaseModel):
    admin_phone: str


class VoiceCallResponse(BaseModel):
    call_id: str | None = None
    status: str
    message: str
    ticket_id: str


class WebhookResult(BaseModel):
    status: str
    ticket_id: str | None = None
    action: str | None = None
    note: str | None = None
