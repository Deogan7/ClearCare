import uuid

from sqlalchemy import String, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    index: Mapped[int] = mapped_column(Integer, nullable=True)
    facility_name: Mapped[str] = mapped_column(String(500), index=True)
    source_facility_type: Mapped[str] = mapped_column(String(255), nullable=True)
    odhf_facility_type: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(500), nullable=True)
    unit: Mapped[str] = mapped_column(String(100), nullable=True)
    street_no: Mapped[str] = mapped_column(String(50), nullable=True)
    street_name: Mapped[str] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(10), nullable=True, index=True)
    city: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    province: Mapped[str] = mapped_column(String(10), nullable=True, index=True)
    source_format_address: Mapped[str] = mapped_column(String(500), nullable=True)
    csd_name: Mapped[str] = mapped_column(String(255), nullable=True)
    csd_uid: Mapped[str] = mapped_column(String(20), nullable=True)
    pr_uid: Mapped[str] = mapped_column(String(10), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
