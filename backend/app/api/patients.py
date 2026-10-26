from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import AppError
from app.db.session import get_db
from app.models import Encounter, Patient
from app.schemas.clinical import EncounterSummaryOut, PractitionerOut
from app.schemas.patient import PatientCreate, PatientListOut, PatientOut, PatientUpdate

router = APIRouter(prefix="/patients", tags=["patients"], dependencies=[Depends(get_current_user)])


def _next_mrn(db: Session) -> str:
    """No. RM otomatis: RM-<tahun>-<urut 4 digit>."""
    prefix = f"RM-{date.today().year}-"
    last = db.scalar(
        select(func.max(Patient.medical_record_no)).where(
            Patient.medical_record_no.like(f"{prefix}%")
        )
    )
    suffix = last.removeprefix(prefix) if last else ""
    number = int(suffix) + 1 if suffix.isdigit() else 1
    return f"{prefix}{number:04d}"


def _get_or_404(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "PATIENT_NOT_FOUND", "Pasien tidak ditemukan")
    return patient


def _mrn_taken(db: Session, mrn: str, exclude_id: int | None = None) -> bool:
    stmt = select(Patient.id).where(Patient.medical_record_no == mrn)
    if exclude_id is not None:
        stmt = stmt.where(Patient.id != exclude_id)
    return db.scalar(stmt) is not None


@router.get("", response_model=PatientListOut)
def list_patients(
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PatientListOut:
    """Daftar pasien; `?q=` mencari nama atau No. RM."""
    stmt = select(Patient)
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Patient.full_name.ilike(like), Patient.medical_record_no.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Patient.full_name).limit(limit).offset(offset)).all()
    return PatientListOut(items=[PatientOut.model_validate(r) for r in rows], total=total)


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)) -> PatientOut:
    data = payload.model_dump()
    mrn = (data.pop("medical_record_no") or "").strip() or _next_mrn(db)
    if _mrn_taken(db, mrn):
        raise AppError(status.HTTP_409_CONFLICT, "MRN_EXISTS", "No. RM sudah dipakai pasien lain")
    patient = Patient(medical_record_no=mrn, **data)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return PatientOut.model_validate(patient)


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)) -> PatientOut:
    return PatientOut.model_validate(_get_or_404(db, patient_id))


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(
    patient_id: int, payload: PatientUpdate, db: Session = Depends(get_db)
) -> PatientOut:
    patient = _get_or_404(db, patient_id)
    changes = payload.model_dump(exclude_unset=True)
    for required in ("full_name", "birth_date", "gender", "medical_record_no"):
        if required in changes and changes[required] is None:
            raise AppError(422, "VALIDATION_ERROR", f"Field {required} tidak boleh kosong")
    mrn = changes.get("medical_record_no")
    if mrn and _mrn_taken(db, mrn, exclude_id=patient.id):
        raise AppError(status.HTTP_409_CONFLICT, "MRN_EXISTS", "No. RM sudah dipakai pasien lain")
    for key, value in changes.items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return PatientOut.model_validate(patient)


@router.get("/{patient_id}/encounters", response_model=list[EncounterSummaryOut])
def list_patient_encounters(
    patient_id: int, db: Session = Depends(get_db)
) -> list[EncounterSummaryOut]:
    """Riwayat kunjungan pasien (terbaru dulu)."""
    _get_or_404(db, patient_id)
    rows = db.scalars(
        select(Encounter)
        .where(Encounter.patient_id == patient_id)
        .order_by(Encounter.started_at.desc(), Encounter.id.desc())
    ).all()
    return [
        EncounterSummaryOut(
            id=e.id,
            status=e.status,
            reason=e.reason,
            started_at=e.started_at,
            practitioner=PractitionerOut.model_validate(e.practitioner) if e.practitioner else None,
            diagnoses=[c.name for c in e.conditions if c.assertion_status == "PRESENT"],
        )
        for e in rows
    ]
