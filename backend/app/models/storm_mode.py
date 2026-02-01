"""Storm Mode tracking — activation state and appointment conversion audit log."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, Integer, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StormTrigger(str, enum.Enum):
    MANUAL = "manual"
    AUTO = "auto"


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
