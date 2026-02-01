import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, Integer, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ReferralStatus(str, enum.Enum):
    # Step 1: Referral sent to specialist
    SENT_TO_SPECIALIST = "sent_to_specialist"
    # Step 2: Specialist didn't get it — resend
    RESENT_TO_SPECIALIST = "resent_to_specialist"
    # Step 3: Specialist confirmed receipt
    REFERRAL_RECEIVED = "referral_received"
    # Step 4: Waiting for specialist to schedule appointment
    APPOINTMENT_SCHEDULING = "appointment_scheduling"
    # Step 5: Specialist appointment confirmed
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    # Step 6: Patient has been notified about appointment
    PATIENT_NOTIFIED = "patient_notified"
    # Step 7: Appointment completed successfully
    COMPLETED = "completed"
    # Step 8: Patient missed the appointment
    MISSED = "missed"
    # Step 9: Reschedule requested
    RESCHEDULE_REQUESTED = "reschedule_requested"
    # Step 10: Ticket closed
    CLOSED = "closed"


class AppointmentType(str, enum.Enum):
    IN_PERSON = "in_person"
    VIRTUAL = "virtual"
    UNKNOWN = "unknown"


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"))
    status: Mapped[ReferralStatus] = mapped_column(
        Enum(ReferralStatus, values_callable=lambda e: [s.value for s in e]),
        default=ReferralStatus.SENT_TO_SPECIALIST,
    )
    description: Mapped[str] = mapped_column(String, nullable=True)
    referred_to: Mapped[str] = mapped_column(String(255))
    specialist_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    action_date: Mapped[datetime] = mapped_column(DateTime)
    scheduled_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Appointment details (filled in after specialist confirms)
    appointment_type: Mapped[AppointmentType] = mapped_column(
        Enum(AppointmentType, values_callable=lambda e: [s.value for s in e]),
        nullable=True,
    )
    ride_needed: Mapped[bool] = mapped_column(Boolean, nullable=True)
    ride_scheduled_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Workflow tracking
    specialist_call_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_call_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    next_follow_up_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    notes: Mapped[str] = mapped_column(String, nullable=True)
    created_by: Mapped[str] = mapped_column(String(100))  # nurse identifier
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    patient = relationship("Patient", back_populates="referrals")
