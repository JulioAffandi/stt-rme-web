from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.encounter import Encounter
    from app.models.master import DrugMaster, ProcedureMaster


class SoapNote(Base):
    """Catatan SOAP per kunjungan (satu per encounter untuk demo)."""

    __tablename__ = "soap_note"
    __table_args__ = (UniqueConstraint("encounter_id", name="uq_soap_note_encounter"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounter.id"), index=True)
    subjective_text: Mapped[str | None] = mapped_column(Text)
    objective_text: Mapped[str | None] = mapped_column(Text)
    assessment_text: Mapped[str | None] = mapped_column(Text)
    plan_text: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(10), default="manual")  # manual | ai
    verified_by_doctor: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    encounter: Mapped["Encounter"] = relationship(back_populates="soap_note")


class Condition(Base):
    """Diagnosa/condition per kunjungan (gaya FHIR Condition)."""

    __tablename__ = "condition"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounter.id"), index=True)
    icd_code: Mapped[str | None] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(255))
    assertion_status: Mapped[str] = mapped_column(String(15), default="PRESENT")
    source: Mapped[str] = mapped_column(String(10), default="manual")  # manual | ai
    verified_by_doctor: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    encounter: Mapped["Encounter"] = relationship(back_populates="conditions")


class Observation(Base):
    """Observasi: gejala (S), pemeriksaan fisik (O), tanda vital."""

    __tablename__ = "observation"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounter.id"), index=True)
    soap_section: Mapped[str] = mapped_column(String(1))  # S | O
    observation_type: Mapped[str] = mapped_column(
        String(20)
    )  # symptom | physical_exam | vital_sign
    body_site: Mapped[str | None] = mapped_column(String(50))  # mis. "Mata", "Paru"
    value_text: Mapped[str | None] = mapped_column(Text)
    entity_label: Mapped[str | None] = mapped_column(String(30))  # GEJALA | TANDA | ...
    assertion_status: Mapped[str] = mapped_column(String(15), default="PRESENT")
    source: Mapped[str] = mapped_column(String(10), default="manual")
    verified_by_doctor: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    encounter: Mapped["Encounter"] = relationship(back_populates="observations")


class Procedure(Base):
    """Tindakan yang dilakukan pada kunjungan."""

    __tablename__ = "procedure"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounter.id"), index=True)
    procedure_master_id: Mapped[int | None] = mapped_column(ForeignKey("procedure_master.id"))
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    source: Mapped[str] = mapped_column(String(10), default="manual")
    verified_by_doctor: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    encounter: Mapped["Encounter"] = relationship(back_populates="procedures")
    master: Mapped["ProcedureMaster | None"] = relationship()


class MedicationRequest(Base):
    """Resep obat per kunjungan."""

    __tablename__ = "medication_request"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounter.id"), index=True)
    drug_id: Mapped[int | None] = mapped_column(ForeignKey("drug_master.id"))
    name: Mapped[str] = mapped_column(String(255))  # snapshot nama dari master
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit: Mapped[str | None] = mapped_column(String(30))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    dosage_note: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(10), default="manual")
    verified_by_doctor: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    encounter: Mapped["Encounter"] = relationship(back_populates="medications")
    drug: Mapped["DrugMaster | None"] = relationship()
