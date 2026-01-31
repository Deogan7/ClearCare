from datetime import datetime
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.patient import Patient
from app.models.user import User
from app.models.referral import Referral, ReferralStatus
from app.schemas.voice import VerifyReferralRequest, VoiceCallResponse, WebhookResult
from app.services import referral_service, voice_service

router = APIRouter()

# Transcript keyword sets for webhook NLP

_CONFIRMATION_KEYWORDS = [
    "received",
    "confirmed",
    "yes we have",
    "got it",
    "we have the documents",
    "can confirm",
]

_MISSED_KEYWORDS = [
    "missed",
    "couldn't make it",
    "didn't attend",
    "no show",
    "wasn't able",
    "could not make",
]

_RESCHEDULE_KEYWORDS = [
    "reschedule",
    "new appointment",
    "different time",
    "change the date",
    "move it",
    "book another",
]


def _analyze_transcript(transcript: str, call_type: str | None) -> str:
    """Basic keyword matching on a call transcript to determine intent."""
    text = transcript.lower()

    # For verification calls, check confirmation first
    if call_type == "referral_verification":
        for kw in _CONFIRMATION_KEYWORDS:
            if kw in text:
                return "confirmed"

    for kw in _RESCHEDULE_KEYWORDS:
        if kw in text:
            return "reschedule"

    for kw in _MISSED_KEYWORDS:
        if kw in text:
            return "missed"

    return "unknown"


# POST /api/voice/verify-referral/{ticket_id}


@router.post("/verify-referral/{ticket_id}", response_model=VoiceCallResponse)
async def trigger_verification_call(
    ticket_id: str,
    body: VerifyReferralRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger an outbound Vapi call to verify a referral was received."""
    referral = await referral_service.get_referral_by_ticket_id(db, ticket_id)
    if not referral:
        raise HTTPException(status_code=404, detail=f"Referral {ticket_id} not found")

    try:
        result = await voice_service.verify_referral_receipt(referral, body.admin_phone)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Vapi API error: {exc.response.status_code}",
        )

    return VoiceCallResponse(
        call_id=result.get("id"),
        status="initiated",
        message=f"Verification call initiated for referral {ticket_id}",
        ticket_id=ticket_id,
    )


# POST /api/voice/patient-checkin/{patient_id}


@router.post("/patient-checkin/{patient_id}", response_model=VoiceCallResponse)
async def trigger_patient_checkin(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a follow-up call to a patient about their most urgent referral."""
    # Look up patient
    patient_result = await db.execute(
        select(Patient).where(Patient.id == patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    # Find their active referrals (scheduled or missed), eager-load patient
    referral_result = await db.execute(
        select(Referral)
        .where(
            Referral.patient_id == patient_id,
            Referral.status.in_([ReferralStatus.SCHEDULED, ReferralStatus.MISSED]),
        )
        .options(selectinload(Referral.patient))
        .order_by(Referral.scheduled_date.asc())
    )
    referrals = list(referral_result.scalars().all())

    if not referrals:
        raise HTTPException(
            status_code=404,
            detail=f"No active referrals found for patient {patient_id}",
        )

    # Call about the most urgent (earliest) referral
    referral = referrals[0]

    try:
        result = await voice_service.initiate_patient_follow_up_call(referral)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Vapi API error: {exc.response.status_code}",
        )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to initiate call — patient data missing on referral",
        )

    return VoiceCallResponse(
        call_id=result.get("id"),
        status="initiated",
        message=(
            f"Check-in call initiated for {patient.first_name} {patient.last_name} "
            f"regarding referral {referral.ticket_id}"
        ),
        ticket_id=referral.ticket_id,
    )


# POST /api/voice/webhook

@router.post("/webhook", response_model=WebhookResult)
async def vapi_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive call-completion events from Vapi and update referral accordingly."""
    payload = await request.json()

    message = payload.get("message", {})
    msg_type = message.get("type")

    # Only acting on completed call reports
    if msg_type != "end-of-call-report":
        return WebhookResult(status="ignored", note=f"Unhandled message type: {msg_type}")

    # Pull the metadata that we attached when placing the call
    call_data = message.get("call", {})
    metadata = call_data.get("metadata", {})
    ticket_id = metadata.get("ticket_id")
    call_type = metadata.get("call_type")
    transcript = message.get("transcript", "")
    summary = message.get("summary", "")
    ended_reason = message.get("endedReason", "")

    if not ticket_id:
        return WebhookResult(status="ignored", note="No ticket_id in call metadata")

    # Look up the referral
    referral = await referral_service.get_referral_by_ticket_id(db, ticket_id)
    if not referral:
        return WebhookResult(
            status="error", ticket_id=ticket_id, note=f"Referral {ticket_id} not found"
        )

    # Determine intent from transcript
    action = _analyze_transcript(transcript, call_type)

    # Apply state transition and build note
    if action == "confirmed" and referral.status == ReferralStatus.PENDING_CONFIRMATION:
        await referral_service.transition_status(db, referral, ReferralStatus.SCHEDULED)
        note = "[Voice] Referral receipt confirmed via verification call."
    elif action == "missed":
        reason = summary or "not provided"
        note = f"[Voice] Patient reported missed appointment. Reason: {reason}"
    elif action == "reschedule":
        note = "[Voice] Patient requested reschedule. Flagged for nurse follow-up."
    else:
        note = (
            f"[Voice] Call completed ({ended_reason}). "
            f"Summary: {summary or 'none'}"
        )

    # Append timestamped note to the referral
    existing = referral.notes or ""
    ts = datetime.utcnow().isoformat()
    referral.notes = f"{existing}\n[{ts}] {note}".strip()
    await db.commit()

    return WebhookResult(
        status="processed",
        ticket_id=ticket_id,
        action=action,
        note=note,
    )
