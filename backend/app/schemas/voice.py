from pydantic import BaseModel


class VerifyReferralRequest(BaseModel):
    admin_phone: str


class DemoCallRequest(BaseModel):
    phone: str  # Your phone number to receive the call
    step: int  # 1 = specialist verification, 2 = patient follow-up


class VoiceCallResponse(BaseModel):
    call_id: str | None = None
    status: str
    message: str
    ticket_id: str | None = None


class WebhookResult(BaseModel):
    status: str
    ticket_id: str | None = None
    action: str | None = None
    note: str | None = None
