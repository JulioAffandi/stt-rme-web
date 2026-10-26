"""Logika simpan & baca Formulir Pemeriksaan (Fase 2: input manual).

Pemetaan hasil NLP -> form (`mapping.py`) baru dikerjakan di Fase 4.
"""

from decimal import Decimal

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import (
    Condition,
    DrugMaster,
    Encounter,
    Icd10Master,
    MedicationRequest,
    Observation,
    Procedure,
    ProcedureMaster,
    SoapNote,
)
from app.schemas.clinical import (
    DiagnosisOut,
    EncounterDetailOut,
    ExamIn,
    MedicationOut,
    PhysicalExamOut,
    PractitionerOut,
    ProcedureOut,
)
from app.schemas.patient import PatientOut

PHYSICAL_EXAM_TYPE = "physical_exam"


def _invalid(detail: str) -> AppError:
    return AppError(422, "VALIDATION_ERROR", detail)


def save_exam(db: Session, encounter: Encounter, payload: ExamIn) -> None:
    """Simpan form final; menggantikan isi pemeriksaan sebelumnya.

    Data yang disimpan dokter ditandai `verified_by_doctor=True`
    (jejak audit: data AI baru dianggap terverifikasi saat Simpan ditekan).
    """
    # --- validasi referensi master sebelum mengubah apa pun
    diagnoses: list[tuple[str | None, str, str]] = []
    for dx in payload.diagnoses:
        name = dx.name.strip()
        if dx.icd_code:
            master = db.get(Icd10Master, dx.icd_code)
            if master is None:
                raise _invalid(f"Kode ICD-10 tidak ditemukan: {dx.icd_code}")
            name = master.name
        diagnoses.append((dx.icd_code, name, dx.source))

    meds: list[tuple[DrugMaster, int, str]] = []
    for med in payload.medications:
        drug = db.get(DrugMaster, med.drug_id)
        if drug is None:
            raise _invalid(f"Obat tidak ditemukan: id {med.drug_id}")
        meds.append((drug, med.quantity, med.source))

    procs: list[tuple[ProcedureMaster, str]] = []
    for proc in payload.procedures:
        master_proc = db.get(ProcedureMaster, proc.procedure_id)
        if master_proc is None:
            raise _invalid(f"Tindakan tidak ditemukan: id {proc.procedure_id}")
        procs.append((master_proc, proc.source))

    # --- catatan SOAP
    soap = encounter.soap_note
    if soap is None:
        soap = SoapNote(encounter=encounter)
        db.add(soap)
    soap.subjective_text = payload.anamnesis.strip() or None
    soap.plan_text = payload.education.strip() or None
    soap.objective_text = (
        "; ".join(f"{p.body_site}: {p.finding}" for p in payload.physical_exam) or None
    )
    soap.assessment_text = "; ".join(name for _, name, _ in diagnoses) or None
    soap.source = "ai" if _any_ai(payload) else "manual"
    soap.verified_by_doctor = True

    # --- ganti data klinis (cascade delete-orphan)
    encounter.observations[:] = [
        o for o in encounter.observations if o.observation_type != PHYSICAL_EXAM_TYPE
    ]
    encounter.conditions.clear()
    encounter.medications.clear()
    encounter.procedures.clear()
    db.flush()

    for p in payload.physical_exam:
        encounter.observations.append(
            Observation(
                soap_section="O",
                observation_type=PHYSICAL_EXAM_TYPE,
                body_site=p.body_site,
                value_text=p.finding,
                entity_label="TANDA",
                assertion_status="PRESENT",
                source="manual",
                verified_by_doctor=True,
            )
        )
    for code, name, source in diagnoses:
        encounter.conditions.append(
            Condition(
                icd_code=code,
                name=name,
                assertion_status="PRESENT",
                source=source,
                verified_by_doctor=True,
            )
        )
    for drug, qty, source in meds:
        encounter.medications.append(
            MedicationRequest(
                drug_id=drug.id,
                name=drug.name,
                quantity=qty,
                unit=drug.unit,
                unit_price=drug.price,
                source=source,
                verified_by_doctor=True,
            )
        )
    for master_proc, source in procs:
        encounter.procedures.append(
            Procedure(
                procedure_master_id=master_proc.id,
                name=master_proc.name,
                price=master_proc.price,
                source=source,
                verified_by_doctor=True,
            )
        )

    encounter.status = "completed"
    db.commit()
    db.refresh(encounter)


def _any_ai(payload: ExamIn) -> bool:
    return any(
        item.source == "ai"
        for item in [*payload.diagnoses, *payload.medications, *payload.procedures]
    )


def build_detail(db: Session, encounter: Encounter) -> EncounterDetailOut:
    """Susun representasi lengkap kunjungan + data klinisnya."""
    soap = encounter.soap_note
    doctor = encounter.practitioner.full_name if encounter.practitioner else None

    exams = sorted(
        (o for o in encounter.observations if o.observation_type == PHYSICAL_EXAM_TYPE),
        key=lambda o: o.id,
    )
    medications = [
        MedicationOut(
            id=m.id,
            drug_id=m.drug_id,
            name=m.name,
            doctor=doctor,
            unit=m.unit,
            quantity=m.quantity,
            unit_price=float(m.unit_price),
            subtotal=float(Decimal(m.unit_price) * m.quantity),
            source=m.source,
            verified_by_doctor=m.verified_by_doctor,
        )
        for m in sorted(encounter.medications, key=lambda m: m.id)
    ]
    procedures = [
        ProcedureOut(
            id=p.id,
            procedure_id=p.procedure_master_id,
            name=p.name,
            price=float(p.price),
            source=p.source,
            verified_by_doctor=p.verified_by_doctor,
        )
        for p in sorted(encounter.procedures, key=lambda p: p.id)
    ]
    total = sum(m.subtotal for m in medications) + sum(p.price for p in procedures)

    return EncounterDetailOut(
        id=encounter.id,
        status=encounter.status,
        reason=encounter.reason,
        started_at=encounter.started_at,
        patient=PatientOut.model_validate(encounter.patient),
        practitioner=(
            PractitionerOut.model_validate(encounter.practitioner)
            if encounter.practitioner
            else None
        ),
        anamnesis=(soap.subjective_text or "") if soap else "",
        education=(soap.plan_text or "") if soap else "",
        physical_exam=[
            PhysicalExamOut(
                body_site=o.body_site or "",
                finding=o.value_text or "",
                source=o.source,
                verified_by_doctor=o.verified_by_doctor,
            )
            for o in exams
        ],
        diagnoses=[
            DiagnosisOut(
                id=c.id,
                icd_code=c.icd_code,
                name=c.name,
                assertion_status=c.assertion_status,
                source=c.source,
                verified_by_doctor=c.verified_by_doctor,
            )
            for c in sorted(encounter.conditions, key=lambda c: c.id)
            if c.assertion_status == "PRESENT"
        ],
        medications=medications,
        procedures=procedures,
        total_cost=total,
    )


def get_encounter_or_404(db: Session, encounter_id: int) -> Encounter:
    encounter = db.scalar(select(Encounter).where(Encounter.id == encounter_id))
    if encounter is None:
        raise AppError(
            status.HTTP_404_NOT_FOUND, "ENCOUNTER_NOT_FOUND", "Kunjungan tidak ditemukan"
        )
    return encounter
