"""Storm Mode tracking — activation state, conversion audit, wellness checks, driver notifications."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, Integer, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class StormTrigger(str, enum.Enum):
    MANUAL = "manual"
    AUTO = "auto"


class WellnessCheckStatus(str, enum.Enum):
    PENDING = "pending"
    CALLING = "calling"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DriverNotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"


class StormModeEvent(Base):
    """Tracks each activation / deactivation of Storm Mode."""

    __tablename__ = "storm_mode_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    trigger: Mapped[StormTrigger] = mapped_column(
        Enum(StormTrigger, values_callable=lambda e: [s.value for s in e]),
    )
    window_hours: Mapped[int] = mapped_column(Integer, default=48)
    activated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deactivated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    converted_count: Mapped[int] = mapped_column(Integer, default=0)
    activated_by: Mapped[str] = mapped_column(String(100), nullable=True)


class StormConversionLog(Base):
    """Audit trail for each in-person → virtual conversion."""

    __tablename__ = "storm_conversion_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storm_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("storm_mode_events.id")
    )
    referral_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referrals.id")
    )
    ticket_id: Mapped[str] = mapped_column(String(20))
    previous_type: Mapped[str] = mapped_column(String(20))
    new_type: Mapped[str] = mapped_column(String(20), default="virtual")
    converted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class StormWellnessCheck(Base):
    """Tracks a wellness check call to a high-risk patient during a storm event."""

    __tablename__ = "storm_wellness_checks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storm_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("storm_mode_events.id")
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id")
    )
    status: Mapped[WellnessCheckStatus] = mapped_column(
        Enum(WellnessCheckStatus, values_callable=lambda e: [s.value for s in e]),
        default=WellnessCheckStatus.PENDING,
    )
    vapi_call_id: Mapped[str] = mapped_column(String(100), nullable=True)

    # Results from transcript analysis
    feeling_ok: Mapped[bool] = mapped_column(Boolean, nullable=True)
    has_symptoms: Mapped[bool] = mapped_column(Boolean, nullable=True)
    symptom_details: Mapped[str] = mapped_column(String, nullable=True)
    medication_stocked: Mapped[bool] = mapped_column(Boolean, nullable=True)
    needs_assistance: Mapped[bool] = mapped_column(Boolean, nullable=True)
    assistance_details: Mapped[str] = mapped_column(String, nullable=True)
    transcript_summary: Mapped[str] = mapped_column(String, nullable=True)

    called_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    patient = relationship("Patient", backref="wellness_checks")


class StormDriverNotification(Base):
    """Simulated SMS notification to a volunteer driver when a ride is cancelled due to storm."""

    __tablename__ = "storm_driver_notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storm_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("storm_mode_events.id")
    )
    referral_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("referrals.id")
    )
    ticket_id: Mapped[str] = mapped_column(String(20))
    driver_name: Mapped[str] = mapped_column(String(100), nullable=True)
    driver_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    patient_name: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(String)
    status: Mapped[DriverNotificationStatus] = mapped_column(
        Enum(DriverNotificationStatus, values_callable=lambda e: [s.value for s in e]),
        default=DriverNotificationStatus.SENT,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
