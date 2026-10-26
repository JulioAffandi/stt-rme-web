from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.encounter import Encounter


class Patient(Base):
    """Data pasien. Hanya gunakan data fiktif/sintetis untuk demo."""

    __tablename__ = "patient"

    id: Mapped[int] = mapped_column(primary_key=True)
    medical_record_no: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    birth_date: Mapped[date] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(String(1))  # M | F
    address: Mapped[str | None] = mapped_column(String(500))
    phone_number: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    encounters: Mapped[list["Encounter"]] = relationship(back_populates="patient")
