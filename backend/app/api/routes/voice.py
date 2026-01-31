from fastapi import APIRouter

router = APIRouter()


@router.post("/verify-referral/{ticket_id}")
async def trigger_verification_call(ticket_id: str):
    """Trigger an outbound Vapi call to verify referral receipt."""
    pass


@router.post("/patient-checkin/{patient_id}")
async def trigger_patient_checkin(patient_id: str):
    """Trigger a wellness check-in call to a patient."""
    pass


@router.post("/webhook")
async def vapi_webhook():
    """Receive call status and transcription updates from Vapi."""
    pass
