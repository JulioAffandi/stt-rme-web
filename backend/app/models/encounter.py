from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.clinical import (
        Condition,
        MedicationRequest,
        Observation,
        Procedure,
        SoapNote,
    )
    from app.models.patient import Patient
    from app.models.pipeline import AudioRecording, DictationJob, PipelineLog
    from app.models.user import User


class Encounter(Base):
    """Kunjungan pasien (encounter) — relasi pusat data klinis."""

    __tablename__ = "encounter"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient.id"), index=True)
    practitioner_id: Mapped[int | None] = mapped_column(ForeignKey("app_user.id"), index=True)
    encounter_type: Mapped[str] = mapped_column(String(30), default="rawat_jalan")
    status: Mapped[str] = mapped_column(String(20), default="open")  # open | completed | cancelled
    reason: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["Patient"] = relationship(back_populates="encounters")
    practitioner: Mapped["User | None"] = relationship(back_populates="encounters")
    soap_note: Mapped["SoapNote | None"] = relationship(
        back_populates="encounter", uselist=False, cascade="all, delete-orphan"
    )
    conditions: Mapped[list["Condition"]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )
    observations: Mapped[list["Observation"]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )
    procedures: Mapped[list["Procedure"]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )
    medications: Mapped[list["MedicationRequest"]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )
    audio_recordings: Mapped[list["AudioRecording"]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )
    dictation_jobs: Mapped[list["DictationJob"]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )
    pipeline_logs: Mapped[list["PipelineLog"]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )
