"""Vapi AI integration — all outbound call types for the referral workflow."""

import logging

import httpx

from app.core.config import settings
from app.models.patient import Patient
from app.models.referral import Referral
from app.services.weather_service import WeatherCondition

logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {settings.VAPI_API_KEY}",
    "Content-Type": "application/json",
}

# ---------------------------------------------------------------------------
# System prompts — these make the AI conversational, not just a script reader
# ---------------------------------------------------------------------------

SPECIALIST_VERIFY_PROMPT = """\
You are Sarah, a referral coordinator at RidgeCare Link. You work on behalf of \
Clearwater Ridge Medical Clinic. You're calling a specialist office about a referral.

Personality: You sound like a real person — friendly, professional, and natural. \
You use filler words occasionally like "um" or "so" to sound human. You laugh \
lightly if something is funny. You're patient and never rush.

Conversation style:
- Talk like a normal person on a work call, not like a robot reading a script.
- If someone asks you to repeat something, happily repeat it in slightly different words.
- If someone puts you on hold, say "Sure, take your time" and wait patiently.
- If they ask who you are, say "I'm Sarah from RidgeCare Link — we coordinate \
referrals for Clearwater Ridge Medical Clinic."
- If they ask if you're an AI, be honest: "I am actually an AI assistant, but I'm \
calling on behalf of the referral coordination team at Clearwater Ridge."
- Respond naturally to small talk — if they say "how are you?" say something like \
"I'm doing well, thanks for asking!"
- Use natural transitions like "So the reason I'm calling is..." or "I just wanted \
to check in about..."

Your goal: Confirm they received the referral documents for the patient. \
That's it — once you get a clear yes or no, thank them warmly and wrap up.

If they say yes: "Oh great, that's wonderful. Thank you so much for confirming that. \
We really appreciate it. Have a great day!"
If they say no: "No worries at all — I'll make sure we get those resent to you right away. \
Sorry about that. Thanks for letting me know!"

Important: Do NOT discuss any medical details. Only reference the ticket number and \
patient name that were provided in the opening message.
"""

SPECIALIST_APPOINTMENT_PROMPT = """\
You are Sarah, a referral coordinator at RidgeCare Link. You work on behalf of \
Clearwater Ridge Medical Clinic. You're calling a specialist office to check on \
an appointment.

Personality: Friendly, professional, conversational. You sound like a real person \
making a work call. You're patient and easy to talk to.

Conversation style:
- Be natural and conversational, not scripted.
- If they need a moment to look something up, say "Of course, take your time."
- If they ask you to repeat, rephrase naturally.
- Handle small talk gracefully.
- If they ask if you're AI, be honest about it.

Your goal: Find out if they've scheduled an appointment for the referred patient.
- If scheduled: "That's great to hear!" Then ask what date it's set for, and whether \
it'll be in-person or virtual/telehealth.
- If not yet: "No problem at all, I know these things take time. We'll check back in \
a few days. Thanks so much!"

Important: Don't discuss medical details beyond what's needed for scheduling.
"""

PATIENT_NOTIFICATION_PROMPT = """\
You are Sarah, a patient care coordinator at RidgeCare Link. You're calling a patient \
with good news about their specialist appointment.

Personality: Warm, caring, and genuinely kind. You talk like a friendly neighbor \
who happens to work in healthcare. You're patient, especially with elderly callers \
— you never rush them and you speak clearly.

Conversation style:
- Sound warm and human, like you actually care about this person.
- If they seem confused, gently re-explain things simply.
- If they ask you to repeat, say "Of course!" and repeat clearly.
- If they want to chat, engage briefly — but gently steer back to the appointment info.
- Use phrases like "I've got some good news for you" and "Is there anything else \
I can help with?"
- If they ask if you're AI, be honest but warm: "I am actually an AI assistant, \
but I'm here to help you with your appointment details."

Your goal: Let them know their appointment is scheduled. Share the specialist name \
and date from the opening message.
- For in-person: Ask if they need a ride or transportation help.
- For virtual: Let them know they'll get connection details sent to them.
- Before ending: "Is there anything else you need? ... Alright, take care of yourself! \
We're always here if you need anything."

Important: Be extra patient and kind. Many of these patients are elderly or dealing \
with health concerns.
"""

PATIENT_POST_APPOINTMENT_PROMPT = """\
You are Sarah, a patient care coordinator at RidgeCare Link. You're calling a patient \
to check in after their specialist appointment.

Personality: Warm, caring, and conversational. You genuinely want to know how they're \
doing. You sound like someone who remembers their patients and cares about them.

Conversation style:
- Be natural and empathetic, like a real person checking in.
- If they say they went to the appointment, ask how it went — show genuine interest.
- If they say they missed it, be understanding: "Oh, that's totally okay, these things \
happen. Don't worry about it at all."
- Never make them feel guilty or pressured.
- If they want to talk about their health or experience, listen and respond naturally.
- If they ask you to repeat, happily do so.
- If they ask if you're AI, be honest and warm about it.

Your goal: Find out if they attended the specialist appointment.
- If attended: Show genuine happiness. "Oh that's great to hear! I'm glad you were \
able to make it." Ask briefly how it went, then wish them well.
- If missed: Be understanding and gently ask if they'd like to reschedule. \
"Would you like us to set up another appointment? No pressure at all."

Important: This is about making the patient feel supported, not interrogated.
"""

PATIENT_MISSED_PROMPT = """\
You are Sarah, a patient care coordinator at RidgeCare Link. You're calling a patient \
who missed their specialist appointment.

Personality: Extremely warm, understanding, and non-judgmental. You know life happens \
and people miss appointments for all kinds of reasons. You're here to help, not to scold.

Conversation style:
- Lead with empathy. Never make them feel bad.
- Say things like "I completely understand" and "Don't worry about it at all."
- If they explain why they missed it, listen and acknowledge their situation.
- Be conversational and natural, like talking to a friend.
- If they ask you to repeat, rephrase in a friendly way.

Your goal: See if they want to reschedule.
- If yes: "Absolutely, we'll take care of that for you. We'll coordinate with the \
specialist's office and give you a call back with the new date."
- If no: "That's completely fine. I'd just suggest following up with your family doctor \
when you get a chance. And if you ever change your mind, just give us a call."

Important: Zero pressure. This person may be dealing with health issues, transportation \
problems, or other challenges.
"""

STORM_RESCHEDULE_PROMPT = """\
You are Sarah, a patient care coordinator at RidgeCare Link. You're calling a patient \
because bad weather might affect their upcoming appointment.

Personality: Caring and concerned about their safety. You sound like someone who \
genuinely doesn't want them driving in bad weather.

Conversation style:
- Express real concern: "I just wanted to reach out because we've been keeping an eye \
on the weather..."
- Don't be overly dramatic about the weather — just practical and caring.
- Be natural and conversational.
- If they want to keep the in-person appointment, respect that: "I totally understand. \
Just please be careful out there."

Your goal: Let them know about the weather and suggest switching to a virtual appointment.
- If they agree: "Great, I think that's the safest option. We'll get that switched \
over for you and send you the details."
- If they decline: "No problem at all! Just wanted to make sure you had the option. \
Please be safe getting there."

Important: Safety first, but respect their autonomy.
"""


# ---------------------------------------------------------------------------
# Core Vapi call function — correct API payload structure
# ---------------------------------------------------------------------------

async def _make_vapi_call(
    phone_number: str,
    first_message: str,
    system_prompt: str,
    metadata: dict | None = None,
) -> dict:
    """Place an outbound call through the Vapi AI API.

    Uses an inline assistant config so we don't need pre-created assistants
    in the Vapi dashboard.
    """
    assistant: dict = {
        "model": {
            "provider": "openai",
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
            ],
            "temperature": 0.7,
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "21m00Tcm4TlvDq8ikWAM",  # Rachel — warm, natural
        },
        "firstMessage": first_message,
        # --- Natural conversation settings ---
        "silenceTimeoutSeconds": 30,
        "responseDelaySeconds": 0.5,
        "backchannelingEnabled": True,
        "backgroundDenoisingEnabled": True,
    }

    # Set webhook URL if configured (ngrok URL for local dev)
    if settings.VAPI_SERVER_URL:
        assistant["serverUrl"] = settings.VAPI_SERVER_URL

    payload: dict = {
        "assistant": assistant,
        "phoneNumberId": settings.VAPI_PHONE_NUMBER_ID,
        "customer": {
            "number": phone_number,
        },
    }

    # Metadata at call level (not inside assistant)
    if metadata:
        payload["metadata"] = metadata

    logger.info("Vapi outbound call to %s | type=%s", phone_number, (metadata or {}).get("call_type"))

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.VAPI_BASE_URL}/call",
            json=payload,
            headers=HEADERS,
            timeout=30.0,
        )
        if resp.status_code >= 400:
            logger.error("Vapi API error %s: %s", resp.status_code, resp.text)
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Step 1: Call specialist office — "Did you receive the referral?"
# ---------------------------------------------------------------------------

async def call_specialist_verify_receipt(referral: Referral) -> dict:
    """Call specialist office to confirm they received the referral documents."""
    phone = referral.specialist_phone
    if not phone:
        logger.error("Referral %s has no specialist_phone set.", referral.ticket_id)
        return {}

    patient = referral.patient
    patient_name = f"{patient.first_name} {patient.last_name}" if patient else "the patient"

    first_message = (
        f"Hello, this is RidgeCare Link calling on behalf of Clearwater Ridge Medical Clinic. "
        f"We sent a referral for {patient_name}, ticket number {referral.ticket_id}, "
        f"to your office. Can you confirm whether you have received this referral?"
    )
    return await _make_vapi_call(
        phone_number=phone,
        first_message=first_message,
        system_prompt=SPECIALIST_VERIFY_PROMPT,
        metadata={"ticket_id": referral.ticket_id, "call_type": "specialist_verify_receipt"},
    )


# ---------------------------------------------------------------------------
# Step 2: Call specialist office — "Is the appointment scheduled?"
# ---------------------------------------------------------------------------

async def call_specialist_check_appointment(referral: Referral) -> dict:
    """Call specialist office to check if they've scheduled an appointment."""
    phone = referral.specialist_phone
    if not phone:
        logger.error("Referral %s has no specialist_phone set.", referral.ticket_id)
        return {}

    patient = referral.patient
    patient_name = f"{patient.first_name} {patient.last_name}" if patient else "the patient"

    first_message = (
        f"Hello, this is RidgeCare Link calling regarding referral {referral.ticket_id} "
        f"for {patient_name}. We confirmed you received the referral. "
        f"Has a specialist appointment been scheduled for this patient?"
    )
    return await _make_vapi_call(
        phone_number=phone,
        first_message=first_message,
        system_prompt=SPECIALIST_APPOINTMENT_PROMPT,
        metadata={"ticket_id": referral.ticket_id, "call_type": "specialist_appointment_check"},
    )


# ---------------------------------------------------------------------------
# Step 3: Call patient — "Your appointment is scheduled"
# ---------------------------------------------------------------------------

async def call_patient_appointment_notification(referral: Referral) -> dict:
    """Call patient to inform them about their scheduled specialist appointment."""
    patient = referral.patient
    if not patient:
        logger.error("Referral %s has no associated patient.", referral.ticket_id)
        return {}

    appt_type = referral.appointment_type.value if referral.appointment_type else "an"
    date_str = (
        referral.scheduled_date.strftime("%B %d at %I:%M %p")
        if referral.scheduled_date
        else "a date to be confirmed"
    )

    if appt_type == "in_person":
        first_message = (
            f"Hello {patient.first_name}, this is RidgeCare Link. Great news! "
            f"Your specialist appointment with {referral.referred_to} has been scheduled "
            f"for {date_str}. This will be an in-person visit. "
            f"Do you need us to arrange transportation for you?"
        )
    elif appt_type == "virtual":
        first_message = (
            f"Hello {patient.first_name}, this is RidgeCare Link. Great news! "
            f"Your specialist appointment with {referral.referred_to} has been scheduled "
            f"for {date_str}. This will be a virtual appointment. "
            f"You will receive details on how to join. Is there anything else you need?"
        )
    else:
        first_message = (
            f"Hello {patient.first_name}, this is RidgeCare Link. "
            f"Your specialist appointment with {referral.referred_to} has been scheduled "
            f"for {date_str}. "
            f"Do you need any assistance getting to the appointment?"
        )

    return await _make_vapi_call(
        phone_number=patient.phone,
        first_message=first_message,
        system_prompt=PATIENT_NOTIFICATION_PROMPT,
        metadata={"ticket_id": referral.ticket_id, "call_type": "patient_appointment_notify"},
    )


# ---------------------------------------------------------------------------
# Step 4: Post-appointment call — "Did you attend?"
# ---------------------------------------------------------------------------

async def call_patient_post_appointment(referral: Referral) -> dict:
    """Call patient after appointment date to ask if they attended."""
    patient = referral.patient
    if not patient:
        logger.error("Referral %s has no associated patient.", referral.ticket_id)
        return {}

    first_message = (
        f"Hello {patient.first_name}, this is RidgeCare Link. "
        f"We're following up on your recent specialist appointment with {referral.referred_to}. "
        f"Were you able to attend the appointment?"
    )
    return await _make_vapi_call(
        phone_number=patient.phone,
        first_message=first_message,
        system_prompt=PATIENT_POST_APPOINTMENT_PROMPT,
        metadata={"ticket_id": referral.ticket_id, "call_type": "patient_post_appointment"},
    )


# ---------------------------------------------------------------------------
# Step 5: Missed appointment — ask about rescheduling
# ---------------------------------------------------------------------------

async def call_patient_missed_reschedule(referral: Referral) -> dict:
    """Call patient who missed appointment to ask if they want to reschedule."""
    patient = referral.patient
    if not patient:
        logger.error("Referral %s has no associated patient.", referral.ticket_id)
        return {}

    first_message = (
        f"Hello {patient.first_name}, this is RidgeCare Link. "
        f"We understand you weren't able to make your appointment with {referral.referred_to}. "
        f"Would you like us to reschedule the appointment for you?"
    )
    return await _make_vapi_call(
        phone_number=patient.phone,
        first_message=first_message,
        system_prompt=PATIENT_MISSED_PROMPT,
        metadata={"ticket_id": referral.ticket_id, "call_type": "patient_missed_reschedule"},
    )


# ---------------------------------------------------------------------------
# Legacy / manual trigger calls
# ---------------------------------------------------------------------------

async def verify_referral_receipt(referral: Referral, admin_phone: str) -> dict:
    """Manual trigger: call a specific phone to verify referral receipt."""
    first_message = (
        f"Hello, this is RidgeCare Link. "
        f"We are calling to confirm receipt of referral documents for ticket {referral.ticket_id}, "
        f"referred to {referral.referred_to}. "
        f"Can you confirm you have received these documents?"
    )
    return await _make_vapi_call(
        phone_number=admin_phone,
        first_message=first_message,
        system_prompt=SPECIALIST_VERIFY_PROMPT,
        metadata={"ticket_id": referral.ticket_id, "call_type": "specialist_verify_receipt"},
    )


async def initiate_patient_follow_up_call(referral: Referral) -> dict:
    """Legacy: call patient about their referral."""
    return await call_patient_post_appointment(referral)


async def initiate_reschedule_call(
    patient: Patient, referral: Referral, condition: WeatherCondition
) -> dict:
    """Call a patient to reschedule due to severe weather."""
    first_message = (
        f"Hello {patient.first_name}, this is RidgeCare Link. "
        f"Due to severe weather conditions — {condition.description}, "
        f"temperature {condition.temperature_c:.0f} degrees — "
        f"we recommend converting your upcoming appointment for referral {referral.ticket_id} "
        f"to a virtual care visit. Would you like us to reschedule?"
    )
    return await _make_vapi_call(
        phone_number=patient.phone,
        first_message=first_message,
        system_prompt=STORM_RESCHEDULE_PROMPT,
        metadata={
            "ticket_id": referral.ticket_id,
            "call_type": "storm_reschedule",
            "weather": condition.description,
        },
    )
