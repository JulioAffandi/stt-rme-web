from datetime import datetime, time

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import AppError
from app.db.session import get_db
from app.models import Encounter, Patient, User
from app.schemas.clinical import EncounterCreate, EncounterDetailOut, ExamIn
from app.services.exam import build_detail, get_encounter_or_404, save_exam

router = APIRouter(tags=["encounters"], dependencies=[Depends(get_current_user)])


@router.post("/encounters", response_model=EncounterDetailOut, status_code=status.HTTP_201_CREATED)
def create_encounter(
    payload: EncounterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EncounterDetailOut:
    """Buat kunjungan baru. `practitioner_id` default = user yang login."""
    if db.get(Patient, payload.patient_id) is None:
        raise AppError(status.HTTP_404_NOT_FOUND, "PATIENT_NOT_FOUND", "Pasien tidak ditemukan")
    practitioner_id = payload.practitioner_id or current_user.id
    if db.get(User, practitioner_id) is None:
        raise AppError(422, "VALIDATION_ERROR", "Dokter tidak ditemukan")
    encounter = Encounter(
        patient_id=payload.patient_id,
        practitioner_id=practitioner_id,
        reason=payload.reason,
        status="open",
    )
    db.add(encounter)
    db.commit()
    db.refresh(encounter)
    return build_detail(db, encounter)


@router.get("/encounters/{encounter_id}", response_model=EncounterDetailOut)
def get_encounter(encounter_id: int, db: Session = Depends(get_db)) -> EncounterDetailOut:
    """Data kunjungan + semua data klinis."""
    return build_detail(db, get_encounter_or_404(db, encounter_id))


@router.post("/encounters/{encounter_id}/exam", response_model=EncounterDetailOut)
def save_encounter_exam(
    encounter_id: int, payload: ExamIn, db: Session = Depends(get_db)
) -> EncounterDetailOut:
    """Simpan Formulir Hasil Pemeriksaan Dokter."""
    encounter = get_encounter_or_404(db, encounter_id)
    if encounter.status == "cancelled":
        raise AppError(
            status.HTTP_409_CONFLICT, "ENCOUNTER_CANCELLED", "Kunjungan sudah dibatalkan"
        )
    save_exam(db, encounter, payload)
    return build_detail(db, encounter)


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)) -> dict[str, int]:
    """Ringkasan dashboard: jumlah pasien & kunjungan hari ini."""
    start_of_day = datetime.combine(datetime.now().date(), time.min)
    patients = db.scalar(select(func.count()).select_from(Patient)) or 0
    today = (
        db.scalar(
            select(func.count()).select_from(Encounter).where(Encounter.started_at >= start_of_day)
        )
        or 0
    )
    return {"patient_count": patients, "encounters_today": today}
