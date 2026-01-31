"""Vapi AI integration — outbound verification calls and patient wellness loops."""

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


async def _make_vapi_call(phone_number: str, message: str, metadata: dict | None = None) -> dict:
    """Place an outbound call through the Vapi AI API."""
    payload = {
        "phoneNumber": phone_number,
        "assistantOverrides": {
            "firstMessage": message,
            "metadata": metadata or {},
        },
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.VAPI_BASE_URL}/call/phone",
            json=payload,
            headers=HEADERS,
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()


async def verify_referral_receipt(referral: Referral, admin_phone: str) -> dict:
    """Call a hospital admin to confirm they received a referral's documents."""
    message = (
        f"Hello, this is an automated call from RidgeCare Link. "
        f"We are calling to confirm receipt of referral documents for ticket {referral.ticket_id}, "
        f"referred to {referral.referred_to}. "
        f"Can you confirm you have received these documents?"
    )
    logger.info("Verifying referral receipt for %s with admin at %s.", referral.ticket_id, admin_phone)
    return await _make_vapi_call(
        phone_number=admin_phone,
        message=message,
        metadata={"ticket_id": referral.ticket_id, "call_type": "referral_verification"},
    )


async def initiate_patient_follow_up_call(referral: Referral) -> dict:
    """Call a patient for post-appointment verification or missed-appointment follow-up."""
    patient = referral.patient
    if not patient:
        logger.error("Referral %s has no associated patient for follow-up call.", referral.ticket_id)
        return {}

    message = (
        f"Hello {patient.first_name}, this is RidgeCare Link calling about your appointment "
        f"for referral {referral.ticket_id}. "
        f"We noticed your appointment may not have been attended. "
        f"Could you let us know if you were able to make it or if you need to reschedule?"
    )
    logger.info("Follow-up call for referral %s to patient %s.", referral.ticket_id, patient.id)
    return await _make_vapi_call(
        phone_number=patient.phone,
        message=message,
        metadata={"ticket_id": referral.ticket_id, "call_type": "patient_follow_up"},
    )


async def initiate_reschedule_call(
    patient: Patient, referral: Referral, condition: WeatherCondition
) -> dict:
    """Call a patient to reschedule a physical visit into a virtual care appointment due to weather."""
    message = (
        f"Hello {patient.first_name}, this is RidgeCare Link. "
        f"Due to severe weather conditions — {condition.description}, "
        f"temperature {condition.temperature_c:.0f} degrees — "
        f"we recommend converting your upcoming appointment for referral {referral.ticket_id} "
        f"to a virtual care visit. Would you like us to reschedule?"
    )
    logger.info(
        "Storm reschedule call for referral %s to patient %s.", referral.ticket_id, patient.id
    )
    return await _make_vapi_call(
        phone_number=patient.phone,
        message=message,
        metadata={
            "ticket_id": referral.ticket_id,
            "call_type": "storm_reschedule",
            "weather": condition.description,
        },
    )
