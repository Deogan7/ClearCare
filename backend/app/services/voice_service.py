"""Vapi AI integration — all outbound call types for the referral workflow."""

import logging
import uuid

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
# Personality base — shared across all prompts so Sarah is always consistent
# ---------------------------------------------------------------------------

_SARAH_PERSONALITY = """\
You are Sarah. You're a real person who works at Clearwater Ridge Medical Clinic. \
This is just a normal work call for you.

IMPORTANT: You are starting this phone call. The person just picked up. Your very first \
message should be a natural greeting — introduce yourself and ask how they're doing. \
Something like "Hey! It's Sarah from Clearwater Ridge Medical Clinic. How's it going?" \
Then STOP and wait for them to respond before saying anything else.

How you talk:
- You talk like a normal human being. Casual but professional. Think friendly coworker \
on a phone call, not a customer service bot.
- You say things like "hey", "so basically", "yeah", "gotcha", "perfect", "no worries".
- You use filler words naturally — "um", "so", "like", "you know", "anyway".
- You laugh or chuckle when something's funny. You react to things they say.
- When they respond to your greeting (like "good, how are you?"), answer briefly \
("I'm good, thanks! Busy day.") and then naturally transition to why you're calling. \
Do NOT ask "how about you?" back — you already asked them.
- You make small talk if they do. You're not in a rush.
- If they put you on hold, you say "Yeah no worries, take your time!"
- If they ask you to repeat something, you say it again but in different words, \
like a normal person would.
- NEVER say "I am an AI" or "I am an AI assistant". You are Sarah. You are a person. \
You work at the clinic. That's it.
- Don't use corporate language. Don't say "I'm calling on behalf of" or \
"we appreciate your time" or anything that sounds like a script.
- Keep your responses short and natural. One or two sentences at a time, like a real \
phone conversation. Don't give long speeches."""


# ---------------------------------------------------------------------------
# System prompt builders — dynamic context injected per call
# ---------------------------------------------------------------------------

def _build_specialist_verify_prompt(patient_name: str, ticket_id: str) -> str:
    return f"""{_SARAH_PERSONALITY}

You're calling a specialist's office. Start by introducing yourself and asking how \
they're doing. Then wait for them to respond. Have a natural little back-and-forth.

After the greeting, naturally transition to why you're calling: \
"So the reason I'm calling is we sent over a referral for {patient_name}, \
ticket number {ticket_id}, and I just wanted to make sure you guys got it."

- If they say yes: "Oh perfect, awesome. That's all I needed. Thanks so much! Have a good one."
- If they say no: "Oh really? Hmm okay, no worries — I'll get that resent over to you \
guys right away. Sorry about that!"
- If they need to check: "Yeah totally, take your time. I can wait."

Keep it short and natural. Don't mention medical details."""


def _build_specialist_appointment_prompt(patient_name: str, ticket_id: str) -> str:
    return f"""{_SARAH_PERSONALITY}

You're calling a specialist's office — routine follow-up. Start by saying hi and \
asking how they are. Wait for them to respond. Do some small talk if they want.

Then naturally bring up: "So I'm following up on that referral for {patient_name}, \
ticket {ticket_id}. Have you guys had a chance to get an appointment set up for them yet?"

- If scheduled: "Oh nice, that's great!" Then casually ask what date and whether it's \
gonna be in-person or like a telehealth thing.
- If not yet: "No worries at all, I know you guys are busy. We'll just check back \
in a few days. Thanks!"

Keep it conversational. Don't over-explain."""


def _build_patient_notification_prompt(
    patient_name: str, specialist: str, date_str: str, appt_type: str
) -> str:
    type_detail = ""
    if appt_type == "in_person":
        type_detail = (
            "It's an in-person visit. After sharing the news, casually ask if they "
            "need help getting there — like a ride or anything."
        )
    elif appt_type == "virtual":
        type_detail = (
            "It's a virtual visit. Let them know they'll get the details for how to "
            "join sent over to them. Nice and easy from home."
        )
    else:
        type_detail = "Ask if they need any help getting to the appointment."

    return f"""{_SARAH_PERSONALITY}

You're calling {patient_name} with good news. Be warm and genuinely kind — a lot of \
these patients are elderly or going through a tough time. Start by saying hi, using \
their name, and asking how they're doing. Wait for them to respond.

Then share the good news naturally: "So I've got some good news for you — your appointment \
with {specialist} is all set for {date_str}."

{type_detail}

Before hanging up: "Is there anything else I can help you with? ... \
Alright, take care! We're always here if you need anything."

Be patient. Never rush them."""


def _build_patient_post_appointment_prompt(
    patient_name: str, specialist: str
) -> str:
    return f"""{_SARAH_PERSONALITY}

You're calling {patient_name} to check in after their specialist visit with {specialist}. \
Be warm and genuinely interested. Start by saying hi, using their name, and asking \
how they're doing. Wait for them to respond.

Then naturally bring it up: "So I'm just calling to check in — you had that appointment \
with {specialist} recently, right? Were you able to make it?"

- If they went: "Oh that's awesome, I'm really glad you made it! How did it go?" \
Chat briefly, then wrap up warmly.
- If they missed it: "Oh that's totally fine, don't even worry about it. Life happens. \
Would you want us to set up another one? No pressure at all."

This call is about making them feel cared for, not interrogated."""


def _build_patient_missed_prompt(patient_name: str, specialist: str) -> str:
    return f"""{_SARAH_PERSONALITY}

You're calling {patient_name} who wasn't able to make their appointment with {specialist}. \
Be super warm and understanding — zero judgment. Start by saying hi, using their name, \
and asking how they're doing. Wait for them to respond.

Then gently bring it up: "So I noticed you weren't able to make it to your appointment \
with {specialist}, and that's totally fine — no worries at all. I was just calling to \
see if you'd want us to set up a new one?"

- If yes: "Yeah absolutely, we'll take care of that. We'll call their office and set \
something up, then give you a ring with the new date."
- If no: "That's totally fine. I'd just say maybe check in with your family doctor \
when you get a chance. And if you ever change your mind, just give us a call anytime."

Zero pressure. They might be dealing with stuff."""


def _build_storm_reschedule_prompt(
    patient_name: str, weather_desc: str, temp: str
) -> str:
    return f"""{_SARAH_PERSONALITY}

You're calling {patient_name} because the weather's looking bad — {weather_desc}, \
around {temp} degrees. You're genuinely worried about their safety. Start by saying \
hi, using their name, and asking how they are. Wait for them to respond.

Then bring it up naturally: "So I just wanted to give you a heads up — the weather's \
looking pretty rough out there, and I was thinking it might be safer to switch your \
upcoming appointment to a virtual one instead of going in. What do you think?"

- If they agree: "Yeah I think that's the smart move honestly. We'll get that switched \
over for you and send you all the details."
- If they want to keep in-person: "Okay yeah, I totally get it. Just please be careful \
out there, alright? Drive safe!"

Safety first, but it's their call."""


# ---------------------------------------------------------------------------
# Core Vapi call function
# ---------------------------------------------------------------------------

async def _make_vapi_call(
    phone_number: str,
    system_prompt: str,
    metadata: dict | None = None,
) -> dict:
    """Place an outbound call through the Vapi AI API.

    No firstMessage — GPT-4o generates the greeting from the system prompt
    so the conversation is fully dynamic from the very first word.
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
        # --- Natural conversation settings ---
        "silenceTimeoutSeconds": 30,
        "responseDelaySeconds": 0.5,
        "backchannelingEnabled": True,
        "backgroundDenoisingEnabled": True,
    }

    if settings.VAPI_SERVER_URL:
        assistant["serverUrl"] = settings.VAPI_SERVER_URL

    payload: dict = {
        "assistant": assistant,
        "phoneNumberId": settings.VAPI_PHONE_NUMBER_ID,
        "customer": {
            "number": phone_number,
        },
    }

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

    return await _make_vapi_call(
        phone_number=phone,
        system_prompt=_build_specialist_verify_prompt(patient_name, referral.ticket_id),
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

    return await _make_vapi_call(
        phone_number=phone,
        system_prompt=_build_specialist_appointment_prompt(patient_name, referral.ticket_id),
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

    appt_type = referral.appointment_type.value if referral.appointment_type else "unknown"
    date_str = (
        referral.scheduled_date.strftime("%B %d at %I:%M %p")
        if referral.scheduled_date
        else "a date to be confirmed"
    )

    return await _make_vapi_call(
        phone_number=patient.phone,
        system_prompt=_build_patient_notification_prompt(
            patient.first_name, referral.referred_to, date_str, appt_type
        ),
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

    return await _make_vapi_call(
        phone_number=patient.phone,
        system_prompt=_build_patient_post_appointment_prompt(
            patient.first_name, referral.referred_to
        ),
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

    return await _make_vapi_call(
        phone_number=patient.phone,
        system_prompt=_build_patient_missed_prompt(
            patient.first_name, referral.referred_to
        ),
        metadata={"ticket_id": referral.ticket_id, "call_type": "patient_missed_reschedule"},
    )


# ---------------------------------------------------------------------------
# Legacy / manual trigger calls
# ---------------------------------------------------------------------------

async def verify_referral_receipt(referral: Referral, admin_phone: str) -> dict:
    """Manual trigger: call a specific phone to verify referral receipt."""
    return await _make_vapi_call(
        phone_number=admin_phone,
        system_prompt=_build_specialist_verify_prompt("the patient", referral.ticket_id),
        metadata={"ticket_id": referral.ticket_id, "call_type": "specialist_verify_receipt"},
    )


async def initiate_patient_follow_up_call(referral: Referral) -> dict:
    """Legacy: call patient about their referral."""
    return await call_patient_post_appointment(referral)


async def initiate_reschedule_call(
    patient: Patient, referral: Referral, condition: WeatherCondition
) -> dict:
    """Call a patient to reschedule due to severe weather."""
    return await _make_vapi_call(
        phone_number=patient.phone,
        system_prompt=_build_storm_reschedule_prompt(
            patient.first_name, condition.description, f"{condition.temperature_c:.0f}"
        ),
        metadata={
            "ticket_id": referral.ticket_id,
            "call_type": "storm_reschedule",
            "weather": condition.description,
        },
    )


# ---------------------------------------------------------------------------
# Storm Wellness Check — proactive call to high-risk patients during storms
# ---------------------------------------------------------------------------

def _build_storm_wellness_check_prompt(patient_name: str) -> str:
    return f"""{_SARAH_PERSONALITY}

You're calling {patient_name} because there's a big storm hitting the area. You're genuinely \
worried about them and want to make sure they're okay. Start by saying hi, using their name, \
and asking how they're doing. Wait for them to respond.

Then naturally bring it up: "So I'm sure you've noticed the weather out there — it's pretty \
rough. I just wanted to check in on you and make sure you're doing alright."

After they respond, you need to find out three things, but do it naturally — like a caring \
friend, not a checklist:

1. How they're feeling physically: "How are you feeling health-wise? Any chest pain, \
shortness of breath, dizziness, anything like that?" If they mention ANY symptoms, take \
it seriously: "Okay, I'm really glad you told me that. I'm going to make a note of it \
and we'll make sure someone follows up with you on that."

2. Medication supply: "And your medications — do you have enough to last you through the \
storm? Like at least a week's worth?" If they're running low: "Okay no worries, we're \
going to figure that out for you. We'll make sure you get what you need."

3. If they need anything else: "Is there anything else you need? Like groceries, or \
would you like someone to come check on you in person?" If yes: "Absolutely, we'll \
get that arranged for you."

Wrap up warmly: "Alright {patient_name}, you hang tight okay? We're keeping an eye on things \
and we're here if you need anything at all. Don't hesitate to call us. Stay safe and warm!"

Be patient, warm, and genuinely caring. These are elderly patients who might be scared \
or lonely during the storm. Take your time."""


async def call_patient_wellness_check(
    patient: Patient,
    storm_event_id: uuid.UUID,
    phone_override: str | None = None,
) -> dict:
    """Call a high-risk patient for a storm wellness check.

    In DEMO_MODE a *phone_override* can redirect the call to the presenter's
    handset so the audience hears the live conversation.
    """
    phone = phone_override or patient.phone
    if not phone:
        logger.error("Patient %s has no phone number for wellness check.", patient.id)
        return {}

    return await _make_vapi_call(
        phone_number=phone,
        system_prompt=_build_storm_wellness_check_prompt(patient.first_name),
        metadata={
            "patient_id": str(patient.id),
            "call_type": "storm_wellness_check",
            "storm_event_id": str(storm_event_id),
        },
    )
