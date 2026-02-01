import uuid as _uuid
from datetime import datetime
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.patient import Patient
from app.models.user import User
from app.models.referral import Referral, ReferralStatus, AppointmentType
from app.models.storm_mode import StormWellnessCheck, WellnessCheckStatus
from app.schemas.voice import (
    VerifyReferralRequest, VoiceCallResponse, WebhookResult, DemoCallRequest,
)
from app.services import referral_service, voice_service

router = APIRouter()

# ---------------------------------------------------------------------------
# Transcript keyword sets for webhook NLP
# ---------------------------------------------------------------------------

_YES_KEYWORDS = [
    "received", "confirmed", "yes we have", "got it",
    "we have the documents", "can confirm", "yes", "that's correct",
    "we got it", "it's here", "affirmative",
]

_NO_KEYWORDS = [
    "no", "haven't received", "don't have", "not yet",
    "we haven't", "nothing here", "no record",
]

_SCHEDULED_KEYWORDS = [
    "scheduled", "booked", "appointment is set", "confirmed appointment",
    "yes it's scheduled", "appointment has been", "booked for",
]

_IN_PERSON_KEYWORDS = [
    "in person", "in-person", "come in", "physical visit",
    "at the office", "at the clinic",
]

_VIRTUAL_KEYWORDS = [
    "virtual", "telehealth", "video call", "online",
    "remote", "phone appointment",
]

_ATTENDED_KEYWORDS = [
    "yes i attended", "i went", "i was there", "yes i did",
    "it went well", "i made it", "attended", "yes",
]

_MISSED_KEYWORDS = [
    "missed", "couldn't make it", "didn't attend", "no show",
    "wasn't able", "could not make", "didn't go", "no",
]

_RESCHEDULE_KEYWORDS = [
    "reschedule", "new appointment", "different time",
    "change the date", "move it", "book another", "yes please reschedule",
]

_NO_RESCHEDULE_KEYWORDS = [
    "no reschedule", "don't reschedule", "no thank you",
    "talk to my doctor", "see my local doctor", "no thanks",
]

_RIDE_YES_KEYWORDS = [
    "yes", "need a ride", "transportation", "please arrange",
    "that would be great", "yes please",
]

_RIDE_NO_KEYWORDS = [
    "no", "i'm fine", "i have a ride", "no thanks",
    "i can get there", "don't need",
]

# Storm wellness check keyword sets
_SYMPTOM_KEYWORDS = [
    "chest pain", "shortness of breath", "dizzy", "dizziness",
    "can't breathe", "heart", "pain", "nauseous", "weak",
    "fell", "fallen", "hurt", "bleeding", "fever", "confused",
]

_FEELING_OK_KEYWORDS = [
    "i'm fine", "doing well", "i'm good", "feeling good",
    "no complaints", "doing okay", "feeling alright", "pretty good",
    "can't complain", "all good",
]

_MEDICATION_OK_KEYWORDS = [
    "enough medication", "stocked up", "plenty", "i'm good on meds",
    "have enough", "week's worth", "enough to last", "refilled",
    "picked up my prescription", "got my meds", "yes i do",
]

_MEDICATION_LOW_KEYWORDS = [
    "running low", "almost out", "need a refill", "don't have enough",
    "only a few days", "ran out", "need more", "short on",
    "forgot to refill", "couldn't get", "pharmacy was closed",
]

_NEEDS_HELP_KEYWORDS = [
    "need groceries", "need food", "could use some help",
    "check on me", "come by", "someone to visit",
    "need supplies", "running low on food", "yes please",
]

_NO_HELP_KEYWORDS = [
    "i'm all set", "don't need anything", "i'm fine",
    "no thank you", "got everything", "neighbor helps",
    "family is here", "son is here", "daughter is here",
]


def _match_keywords(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def _analyze_specialist_receipt(transcript: str) -> str:
    if _match_keywords(transcript, _YES_KEYWORDS):
        return "yes"
    if _match_keywords(transcript, _NO_KEYWORDS):
        return "no"
    return "unknown"


def _analyze_appointment_scheduled(transcript: str) -> dict:
    result = {"scheduled": False, "appointment_type": None}
    if _match_keywords(transcript, _SCHEDULED_KEYWORDS):
        result["scheduled"] = True
        if _match_keywords(transcript, _IN_PERSON_KEYWORDS):
            result["appointment_type"] = "in_person"
        elif _match_keywords(transcript, _VIRTUAL_KEYWORDS):
            result["appointment_type"] = "virtual"
    return result


def _analyze_patient_notification(transcript: str) -> dict:
    result = {"ride_needed": None, "appointment_type": None}
    if _match_keywords(transcript, _RIDE_YES_KEYWORDS):
        result["ride_needed"] = True
    elif _match_keywords(transcript, _RIDE_NO_KEYWORDS):
        result["ride_needed"] = False
    if _match_keywords(transcript, _IN_PERSON_KEYWORDS):
        result["appointment_type"] = "in_person"
    elif _match_keywords(transcript, _VIRTUAL_KEYWORDS):
        result["appointment_type"] = "virtual"
    return result


def _analyze_post_appointment(transcript: str) -> str:
    if _match_keywords(transcript, _ATTENDED_KEYWORDS):
        return "attended"
    if _match_keywords(transcript, _MISSED_KEYWORDS):
        return "missed"
    return "unknown"


def _analyze_reschedule(transcript: str) -> str:
    if _match_keywords(transcript, _RESCHEDULE_KEYWORDS):
        return "yes"
    if _match_keywords(transcript, _NO_RESCHEDULE_KEYWORDS):
        return "no"
    return "unknown"


def _analyze_wellness_check(transcript: str) -> dict:
    """Analyze a storm wellness check call transcript."""
    has_symptoms = _match_keywords(transcript, _SYMPTOM_KEYWORDS)
    feeling_ok = _match_keywords(transcript, _FEELING_OK_KEYWORDS) and not has_symptoms
    medication_ok = _match_keywords(transcript, _MEDICATION_OK_KEYWORDS)
    medication_low = _match_keywords(transcript, _MEDICATION_LOW_KEYWORDS)
    needs_help = _match_keywords(transcript, _NEEDS_HELP_KEYWORDS)
    no_help = _match_keywords(transcript, _NO_HELP_KEYWORDS)

    return {
        "feeling_ok": feeling_ok if (feeling_ok or has_symptoms) else None,
        "has_symptoms": has_symptoms,
        "medication_stocked": (
            True if medication_ok and not medication_low
            else False if medication_low
            else None
        ),
        "needs_assistance": (
            True if needs_help and not no_help
            else False if no_help
            else None
        ),
    }


def _extract_context_around(transcript: str, keywords: list[str]) -> str:
    """Extract a brief snippet around matched keywords from the transcript."""
    text_lower = transcript.lower()
    for kw in keywords:
        idx = text_lower.find(kw)
        if idx >= 0:
            start = max(0, idx - 50)
            end = min(len(transcript), idx + len(kw) + 100)
            return f"...{transcript[start:end]}..."
    return ""


# ---------------------------------------------------------------------------
# DEMO endpoint — simplified 2-call flow for live presentations
# ---------------------------------------------------------------------------
# Step 1: SENT_TO_SPECIALIST → (calls your phone as "specialist") → REFERRAL_RECEIVED
# Step 2: REFERRAL_RECEIVED  → (calls your phone as "patient")    → COMPLETED → CLOSED
# ---------------------------------------------------------------------------

@router.post("/demo/{ticket_id}", response_model=VoiceCallResponse)
async def demo_call(
    ticket_id: str,
    body: DemoCallRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a demo call. Step 1 = specialist verification, Step 2 = patient follow-up.

    Both calls go to the phone number you provide so you can play both roles.
    """
    referral = await referral_service.get_referral_by_ticket_id(db, ticket_id)
    if not referral:
        raise HTTPException(status_code=404, detail=f"Referral {ticket_id} not found")

    patient = referral.patient
    patient_name = f"{patient.first_name} {patient.last_name}" if patient else "the patient"

    if body.step == 1:
        # --- Demo Step 1: Call "specialist" to verify receipt ---
        try:
            result = await voice_service._make_vapi_call(
                phone_number=body.phone,
                system_prompt=voice_service._build_specialist_verify_prompt(
                    patient_name, referral.ticket_id
                ),
                metadata={
                    "ticket_id": referral.ticket_id,
                    "call_type": "demo_specialist_verify",
                },
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"Vapi API error {exc.response.status_code}: {exc.response.text}")

        await referral_service.record_call_attempt(db, referral)
        return VoiceCallResponse(
            call_id=result.get("id"),
            status="initiated",
            message=f"Demo Step 1: Calling {body.phone} as specialist for {ticket_id}",
            ticket_id=ticket_id,
        )

    elif body.step == 2:
        # --- Demo Step 2: Call "patient" for post-appointment follow-up ---
        try:
            result = await voice_service._make_vapi_call(
                phone_number=body.phone,
                system_prompt=voice_service._build_patient_post_appointment_prompt(
                    patient_name, referral.referred_to
                ),
                metadata={
                    "ticket_id": referral.ticket_id,
                    "call_type": "demo_patient_followup",
                },
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"Vapi API error {exc.response.status_code}: {exc.response.text}")

        return VoiceCallResponse(
            call_id=result.get("id"),
            status="initiated",
            message=f"Demo Step 2: Calling {body.phone} as patient for {ticket_id}",
            ticket_id=ticket_id,
        )

    else:
        raise HTTPException(status_code=422, detail="step must be 1 or 2")


# ---------------------------------------------------------------------------
# Manual trigger endpoints (full workflow)
# ---------------------------------------------------------------------------

@router.post("/verify-referral/{ticket_id}", response_model=VoiceCallResponse)
async def trigger_verification_call(
    ticket_id: str,
    body: VerifyReferralRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger a call to specialist to verify referral receipt."""
    referral = await referral_service.get_referral_by_ticket_id(db, ticket_id)
    if not referral:
        raise HTTPException(status_code=404, detail=f"Referral {ticket_id} not found")

    try:
        result = await voice_service.verify_referral_receipt(referral, body.admin_phone)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Vapi API error: {exc.response.status_code}")

    return VoiceCallResponse(
        call_id=result.get("id"),
        status="initiated",
        message=f"Verification call initiated for referral {ticket_id}",
        ticket_id=ticket_id,
    )


@router.post("/trigger-workflow-call/{ticket_id}", response_model=VoiceCallResponse)
async def trigger_workflow_call(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger the next appropriate call in the workflow for a referral."""
    referral = await referral_service.get_referral_by_ticket_id(db, ticket_id)
    if not referral:
        raise HTTPException(status_code=404, detail=f"Referral {ticket_id} not found")

    call_fn = None
    msg = ""

    if referral.status in (ReferralStatus.SENT_TO_SPECIALIST, ReferralStatus.RESENT_TO_SPECIALIST):
        call_fn = voice_service.call_specialist_verify_receipt
        msg = "Specialist receipt verification call initiated"
    elif referral.status in (ReferralStatus.REFERRAL_RECEIVED, ReferralStatus.APPOINTMENT_SCHEDULING):
        call_fn = voice_service.call_specialist_check_appointment
        msg = "Specialist appointment check call initiated"
    elif referral.status == ReferralStatus.APPOINTMENT_SCHEDULED:
        call_fn = voice_service.call_patient_appointment_notification
        msg = "Patient appointment notification call initiated"
    elif referral.status == ReferralStatus.PATIENT_NOTIFIED:
        call_fn = voice_service.call_patient_post_appointment
        msg = "Post-appointment follow-up call initiated"
    elif referral.status == ReferralStatus.MISSED:
        call_fn = voice_service.call_patient_missed_reschedule
        msg = "Missed appointment reschedule call initiated"
    else:
        raise HTTPException(
            status_code=422,
            detail=f"No call action available for status '{referral.status.value}'",
        )

    try:
        result = await call_fn(referral)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Vapi API error: {exc.response.status_code}")

    if not result:
        raise HTTPException(status_code=500, detail="Failed to initiate call — missing phone or patient data")

    await referral_service.record_call_attempt(db, referral)

    return VoiceCallResponse(
        call_id=result.get("id"),
        status="initiated",
        message=f"{msg} for {ticket_id}",
        ticket_id=ticket_id,
    )


@router.post("/patient-checkin/{patient_id}", response_model=VoiceCallResponse)
async def trigger_patient_checkin(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a follow-up call to a patient about their most urgent referral."""
    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    referral_result = await db.execute(
        select(Referral)
        .where(
            Referral.patient_id == patient_id,
            Referral.status.in_([
                ReferralStatus.APPOINTMENT_SCHEDULED,
                ReferralStatus.PATIENT_NOTIFIED,
                ReferralStatus.MISSED,
            ]),
        )
        .options(selectinload(Referral.patient))
        .order_by(Referral.scheduled_date.asc())
    )
    referrals = list(referral_result.scalars().all())

    if not referrals:
        raise HTTPException(status_code=404, detail=f"No active referrals for patient {patient_id}")

    referral = referrals[0]

    try:
        result = await voice_service.call_patient_post_appointment(referral)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Vapi API error {exc.response.status_code}: {exc.response.text}")

    if not result:
        raise HTTPException(status_code=500, detail="Failed to initiate call — patient data missing")

    return VoiceCallResponse(
        call_id=result.get("id"),
        status="initiated",
        message=(
            f"Check-in call initiated for {patient.first_name} {patient.last_name} "
            f"regarding referral {referral.ticket_id}"
        ),
        ticket_id=referral.ticket_id,
    )


# ---------------------------------------------------------------------------
# Webhook — processes ALL call types from Vapi (including demo calls)
# ---------------------------------------------------------------------------

@router.post("/webhook", response_model=WebhookResult)
async def vapi_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive call-completion events from Vapi and update referral accordingly."""
    payload = await request.json()

    message = payload.get("message", {})
    msg_type = message.get("type")

    if msg_type != "end-of-call-report":
        return WebhookResult(status="ignored", note=f"Unhandled message type: {msg_type}")

    call_data = message.get("call", {})
    # Vapi may put metadata at call level or nested — check both
    metadata = call_data.get("metadata", {}) or {}
    if not metadata.get("ticket_id"):
        metadata = message.get("metadata", {}) or {}
    ticket_id = metadata.get("ticket_id")
    call_type = metadata.get("call_type")
    transcript = message.get("transcript", "")
    summary = message.get("summary", "")
    ended_reason = message.get("endedReason", "")

    # --- Storm Wellness Check — handled separately (patient-level, not referral-level) ---
    if call_type == "storm_wellness_check":
        patient_id = metadata.get("patient_id")
        storm_event_id = metadata.get("storm_event_id")

        if not patient_id or not storm_event_id:
            return WebhookResult(status="error", note="Missing patient_id or storm_event_id in wellness check metadata")

        result = _analyze_wellness_check(transcript)

        wc_result = await db.execute(
            select(StormWellnessCheck).where(
                StormWellnessCheck.patient_id == _uuid.UUID(patient_id),
                StormWellnessCheck.storm_event_id == _uuid.UUID(storm_event_id),
            )
        )
        wellness_check = wc_result.scalar_one_or_none()

        if wellness_check:
            wellness_check.status = WellnessCheckStatus.COMPLETED
            wellness_check.feeling_ok = result["feeling_ok"]
            wellness_check.has_symptoms = result["has_symptoms"]
            wellness_check.medication_stocked = result["medication_stocked"]
            wellness_check.needs_assistance = result["needs_assistance"]
            wellness_check.transcript_summary = summary or transcript[:500]
            wellness_check.completed_at = datetime.utcnow()

            if result["has_symptoms"]:
                wellness_check.symptom_details = _extract_context_around(transcript, _SYMPTOM_KEYWORDS)
            if result["needs_assistance"]:
                wellness_check.assistance_details = _extract_context_around(transcript, _NEEDS_HELP_KEYWORDS)

            await db.commit()

            flags = []
            if result["has_symptoms"]:
                flags.append("SYMPTOMS REPORTED")
            if result["medication_stocked"] is False:
                flags.append("LOW ON MEDICATION")
            if result["needs_assistance"]:
                flags.append("NEEDS ASSISTANCE")

            note = f"[Storm Wellness] Check completed for patient {patient_id}."
            if flags:
                note += f" ALERTS: {', '.join(flags)}"
            else:
                note += " Patient is doing well."
        else:
            note = f"[Storm Wellness] No wellness check record found for patient {patient_id}."

        return WebhookResult(status="processed", action="wellness_check_completed", note=note)

    # --- All other call types require a ticket_id (referral-level) ---
    if not ticket_id:
        return WebhookResult(status="ignored", note="No ticket_id in call metadata")

    referral = await referral_service.get_referral_by_ticket_id(db, ticket_id)
    if not referral:
        return WebhookResult(status="error", ticket_id=ticket_id, note=f"Referral {ticket_id} not found")

    action = "unknown"
    note = ""

    # =======================================================================
    # DEMO CALL TYPES — simplified transitions for live presentations
    # These bypass the state machine and set status directly.
    # =======================================================================

    if call_type == "demo_specialist_verify":
        result = _analyze_specialist_receipt(transcript)
        if result == "yes":
            referral.status = ReferralStatus.REFERRAL_RECEIVED
            await db.commit()
            action = "demo_referral_received"
            note = "[Demo] Specialist confirmed receipt. Status → REFERRAL_RECEIVED. Ready for Step 2."
        elif result == "no":
            referral.status = ReferralStatus.RESENT_TO_SPECIALIST
            await db.commit()
            action = "demo_not_received"
            note = "[Demo] Specialist hasn't received referral. Status → RESENT_TO_SPECIALIST. Try Step 1 again."
        else:
            action = "demo_unclear"
            note = f"[Demo] Specialist response unclear. Try Step 1 again. Transcript: {transcript[:200]}"

    elif call_type == "demo_patient_followup":
        result = _analyze_post_appointment(transcript)
        if result == "attended":
            referral.status = ReferralStatus.COMPLETED
            await db.commit()
            referral.status = ReferralStatus.CLOSED
            await db.commit()
            action = "demo_completed"
            note = "[Demo] Patient confirmed attendance. Status → COMPLETED → CLOSED. Demo complete!"
        elif result == "missed":
            referral.status = ReferralStatus.MISSED
            await db.commit()
            action = "demo_missed"
            note = "[Demo] Patient reported missed appointment. Status → MISSED."
        else:
            action = "demo_unclear"
            note = f"[Demo] Patient response unclear. Try Step 2 again. Transcript: {transcript[:200]}"

    # =======================================================================
    # PRODUCTION CALL TYPES — full state machine with validation
    # =======================================================================

    elif call_type == "specialist_verify_receipt":
        result = _analyze_specialist_receipt(transcript)
        if result == "yes":
            await referral_service.transition_status(db, referral, ReferralStatus.REFERRAL_RECEIVED)
            if settings.DEMO_MODE:
                await referral_service.schedule_next_follow_up(db, referral, hours=0)  # immediate
            else:
                await referral_service.schedule_next_follow_up(db, referral, hours=48)
            action = "referral_received"
            note = "[Voice] Specialist confirmed referral receipt. Ticket updated to REFERRAL_RECEIVED."
        elif result == "no":
            await referral_service.transition_status(db, referral, ReferralStatus.RESENT_TO_SPECIALIST)
            if settings.DEMO_MODE:
                await referral_service.schedule_next_follow_up(db, referral, hours=0)
            else:
                await referral_service.schedule_next_follow_up(db, referral, business_days=5)
            action = "not_received"
            note = "[Voice] Specialist has NOT received referral. Resending. Next follow-up in 5 business days."
        else:
            if settings.DEMO_MODE:
                await referral_service.schedule_next_follow_up(db, referral, hours=0)
            else:
                await referral_service.schedule_next_follow_up(db, referral, hours=24)
            action = "unclear"
            note = f"[Voice] Specialist call unclear. Will retry. Summary: {summary or 'none'}"

    elif call_type == "specialist_appointment_check":
        result = _analyze_appointment_scheduled(transcript)
        if result["scheduled"]:
            await referral_service.transition_status(db, referral, ReferralStatus.APPOINTMENT_SCHEDULED)
            if result["appointment_type"] == "in_person":
                referral.appointment_type = AppointmentType.IN_PERSON
            elif result["appointment_type"] == "virtual":
                referral.appointment_type = AppointmentType.VIRTUAL
            await db.commit()
            action = "appointment_scheduled"
            note = f"[Voice] Specialist appointment scheduled ({result['appointment_type'] or 'type TBD'})."
        else:
            if referral.status == ReferralStatus.REFERRAL_RECEIVED:
                await referral_service.transition_status(db, referral, ReferralStatus.APPOINTMENT_SCHEDULING)
            if settings.DEMO_MODE:
                await referral_service.schedule_next_follow_up(db, referral, hours=0)
            else:
                await referral_service.schedule_next_follow_up(db, referral, business_days=2)
            action = "not_scheduled_yet"
            note = "[Voice] Appointment not yet scheduled. Will follow up in 2 business days."

    elif call_type == "patient_appointment_notify":
        result = _analyze_patient_notification(transcript)
        await referral_service.transition_status(db, referral, ReferralStatus.PATIENT_NOTIFIED)

        if result["appointment_type"] == "in_person":
            referral.appointment_type = AppointmentType.IN_PERSON
        elif result["appointment_type"] == "virtual":
            referral.appointment_type = AppointmentType.VIRTUAL

        if result["ride_needed"] is True:
            referral.ride_needed = True
            note = "[Voice] Patient notified. Ride requested — scheduling transportation."
        elif result["ride_needed"] is False:
            referral.ride_needed = False
            note = "[Voice] Patient notified. No ride needed."
        else:
            note = "[Voice] Patient notified about appointment."

        if settings.DEMO_MODE:
            await referral_service.schedule_next_follow_up(db, referral, hours=0)
        elif referral.scheduled_date:
            from app.services.referral_service import _add_business_days
            referral.next_follow_up_at = _add_business_days(referral.scheduled_date, 1)
        else:
            await referral_service.schedule_next_follow_up(db, referral, business_days=1)

        await db.commit()
        action = "patient_notified"

    elif call_type == "patient_post_appointment":
        result = _analyze_post_appointment(transcript)
        if result == "attended":
            await referral_service.transition_status(db, referral, ReferralStatus.COMPLETED)
            await referral_service.transition_status(db, referral, ReferralStatus.CLOSED)
            action = "completed"
            note = "[Voice] Patient confirmed attendance. Ticket CLOSED."
        elif result == "missed":
            await referral_service.transition_status(db, referral, ReferralStatus.MISSED)
            action = "missed"
            note = "[Voice] Patient reported missed appointment. Asking about reschedule."
        else:
            action = "unclear"
            note = f"[Voice] Post-appointment call unclear. Summary: {summary or 'none'}"

    elif call_type == "patient_missed_reschedule":
        result = _analyze_reschedule(transcript)
        if result == "yes":
            await referral_service.transition_status(db, referral, ReferralStatus.RESCHEDULE_REQUESTED)
            await referral_service.transition_status(db, referral, ReferralStatus.SENT_TO_SPECIALIST)
            if settings.DEMO_MODE:
                await referral_service.schedule_next_follow_up(db, referral, hours=0)
            else:
                await referral_service.schedule_next_follow_up(db, referral, hours=48)
            referral.specialist_call_attempts = 0
            await db.commit()
            action = "reschedule_yes"
            note = "[Voice] Patient wants to reschedule. Restarting referral workflow."
        elif result == "no":
            await referral_service.transition_status(db, referral, ReferralStatus.CLOSED)
            action = "reschedule_no"
            note = "[Voice] Patient declined reschedule. Ticket CLOSED. Suggested local doctor follow-up."
        else:
            action = "unclear"
            note = f"[Voice] Reschedule response unclear. Summary: {summary or 'none'}"

    elif call_type == "storm_reschedule":
        if _match_keywords(transcript, _YES_KEYWORDS):
            referral.appointment_type = AppointmentType.VIRTUAL
            await db.commit()
            action = "storm_reschedule_accepted"
            note = "[Voice] Patient accepted virtual care switch due to weather."
        else:
            action = "storm_reschedule_declined"
            note = "[Voice] Patient declined weather reschedule."

    else:
        action = "unknown"
        note = f"[Voice] Call completed ({ended_reason}). Type: {call_type}. Summary: {summary or 'none'}"

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
