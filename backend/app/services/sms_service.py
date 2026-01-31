"""Twilio SMS integration — storm check-ins and virtual care links."""

import logging

from twilio.rest import Client

from app.core.config import settings
from app.models.patient import Patient
from app.services.weather_service import WeatherCondition

logger = logging.getLogger(__name__)


def _get_twilio_client() -> Client:
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


async def send_sms(to: str, body: str) -> str:
    """Send an SMS via Twilio. Returns the message SID."""
    client = _get_twilio_client()
    message = client.messages.create(
        to=to,
        from_=settings.TWILIO_PHONE_NUMBER,
        body=body,
    )
    logger.info("SMS sent to %s (SID: %s).", to, message.sid)
    return message.sid


async def send_storm_checkin_sms(patient: Patient, condition: WeatherCondition) -> str:
    """Send a severe-weather check-in SMS to a high-risk patient."""
    body = (
        f"Hi {patient.first_name}, this is RidgeCare Link. "
        f"Severe weather is expected ({condition.description}, "
        f"{condition.temperature_c:.0f}°C). "
        f"Please stay safe and warm. If you need assistance or "
        f"want to switch an upcoming appointment to virtual care, "
        f"reply YES or call your care team."
    )
    return await send_sms(to=patient.phone, body=body)


async def send_appointment_reminder(patient: Patient, ticket_id: str, date_str: str) -> str:
    """Send an appointment reminder SMS."""
    body = (
        f"Hi {patient.first_name}, this is a reminder from RidgeCare Link. "
        f"You have an upcoming appointment (Ref: {ticket_id}) on {date_str}. "
        f"If you need to reschedule, please reply or contact your care team."
    )
    return await send_sms(to=patient.phone, body=body)


async def send_virtual_care_link(patient: Patient, link: str) -> str:
    """Send a virtual care session link via SMS."""
    body = (
        f"Hi {patient.first_name}, your appointment has been moved to virtual care. "
        f"Join here: {link}"
    )
    return await send_sms(to=patient.phone, body=body)
