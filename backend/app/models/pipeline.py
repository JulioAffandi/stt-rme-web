from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.encounter import Encounter


class AudioRecording(Base):
    """File audio dikte medis."""

    __tablename__ = "audio_recording"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounter.id"), index=True)
    file_path: Mapped[str] = mapped_column(String(512))
    original_filename: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    duration_sec: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    encounter: Mapped["Encounter"] = relationship(back_populates="audio_recordings")


class DictationJob(Base):
    """Job pemrosesan dikte (polling status dari frontend)."""

    __tablename__ = "dictation_job"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounter.id"), index=True)
    audio_id: Mapped[int | None] = mapped_column(ForeignKey("audio_recording.id"))
    status: Mapped[str] = mapped_column(
        String(15), default="queued"
    )  # queued|processing|done|error
    step: Mapped[str | None] = mapped_column(String(50))  # stt|soap|ner|assertion|mapping
    result_json: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    encounter: Mapped["Encounter"] = relationship(back_populates="dictation_jobs")
    audio: Mapped["AudioRecording | None"] = relationship()


class PipelineLog(Base):
    """Log & metrik evaluasi pipeline (WER, SOAP F1, NER F1, latency)."""

    __tablename__ = "pipeline_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int | None] = mapped_column(ForeignKey("encounter.id"), index=True)
    model_version: Mapped[str | None] = mapped_column(String(100))
    wer_value: Mapped[float | None] = mapped_column(Float)
    soap_f1: Mapped[float | None] = mapped_column(Float)
    ner_f1: Mapped[float | None] = mapped_column(Float)
    latency_ms: Mapped[dict | None] = mapped_column(JSON)  # {"stt": .., "soap": .., ..}
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    encounter: Mapped["Encounter | None"] = relationship(back_populates="pipeline_logs")
