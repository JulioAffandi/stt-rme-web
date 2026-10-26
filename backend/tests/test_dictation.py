"""Pengujian untuk modul dikte dan STT (Fase 3)."""

from __future__ import annotations

from app.models.encounter import Encounter
from app.models.patient import Patient
from app.models.user import User
from app.nlp.base import Segment
from app.nlp.stt_whisper import WhisperSttEngine


def _setup_test_encounter(db) -> tuple[User, Encounter]:
    doctor = User(
        email="dokter.stt@uji.id",
        password_hash="test",
        full_name="dr. Uji STT",
        role="doctor",
    )
    db.add(doctor)
    db.flush()

    patient = Patient(
        mrn="RM-20261026-9999",
        full_name="Pasien Uji Dikte",
        gender="M",
    )
    db.add(patient)
    db.flush()

    encounter = Encounter(
        patient_id=patient.id,
        practitioner_id=doctor.id,
        status="in_progress",
    )
    db.add(encounter)
    db.commit()
    db.refresh(encounter)
    return doctor, encounter


def test_list_dictation_samples(client, db):
    user, _ = _setup_test_encounter(db)
    from app.core.security import create_access_token

    token = create_access_token(str(user.id))
    resp = client.get(
        "/api/v1/dictation/samples",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    samples = resp.json()
    assert isinstance(samples, list)
    assert len(samples) >= 1
    assert any(s["id"] == "sample-dbd" for s in samples)


def test_dictation_job_status_404(client, db):
    user, _ = _setup_test_encounter(db)
    from app.core.security import create_access_token

    token = create_access_token(str(user.id))
    resp = client.get(
        "/api/v1/dictation-jobs/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


def test_run_sample_dictation_creates_job(client, db):
    user, encounter = _setup_test_encounter(db)
    from app.core.security import create_access_token

    token = create_access_token(str(user.id))
    resp = client.post(
        f"/api/v1/encounters/{encounter.id}/dictation/sample/sample-dbd",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert "job_id" in body
    assert body["encounter_id"] == encounter.id
    assert body["status"] == "queued"

    job_id = body["job_id"]
    job_resp = client.get(
        f"/api/v1/dictation-jobs/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert job_resp.status_code == 200
    job_data = job_resp.json()
    assert job_data["id"] == job_id


def test_whisper_engine_fallback_result():
    engine = WhisperSttEngine(model_path="non_existent_path")
    assert not engine.load_model()
    # Panggil transcribe pada sample file
    segments = engine.transcribe("data/samples/SAMPLE_DBD.wav")
    assert len(segments) >= 1
    assert all(isinstance(s, Segment) for s in segments)
    assert any("pusing" in s.text.lower() for s in segments)
