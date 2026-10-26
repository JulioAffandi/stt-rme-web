"""Endpoint API untuk dikte medis, rekaman audio, dan polling status job transkripsi."""

from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.core.errors import AppError
from app.models.encounter import Encounter
from app.models.pipeline import AudioRecording, DictationJob
from app.models.user import User
from app.services.audio import convert_to_wav_16k_mono, get_audio_storage_dir, save_uploaded_audio
from app.services.pipeline import execute_dictation_job

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dictation"])


@router.post(
    "/encounters/{encounter_id}/dictation",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Unggah audio dikte medis dan jadwalkan transkripsi Whisper",
)
def upload_dictation_audio(
    encounter_id: int,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Menerima file rekaman audio dari browser atau upload file,

    mengonversinya ke WAV 16kHz mono, dan menjadwalkan job inferensi Whisper di background.
    """
    encounter = db.get(Encounter, encounter_id)
    if not encounter:
        raise AppError(
            status_code=404,
            code="ENCOUNTER_NOT_FOUND",
            detail="Kunjungan tidak ditemukan",
        )

    # Simpan dan konversi file audio
    raw_path, wav_path, duration_sec = save_uploaded_audio(
        file_obj=audio.file,
        filename=audio.filename or "recording.webm",
        encounter_id=encounter.id,
        mime_type=audio.content_type,
    )

    # Catat audio_recording ke database
    recording = AudioRecording(
        encounter_id=encounter.id,
        file_path=raw_path,
        original_filename=audio.filename,
        mime_type=audio.content_type or "audio/webm",
        duration_sec=duration_sec,
    )
    db.add(recording)
    db.flush()

    # Buat dictation_job
    job = DictationJob(
        encounter_id=encounter.id,
        audio_id=recording.id,
        status="queued",
        step="stt",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Jadwalkan background task
    background_tasks.add_task(
        execute_dictation_job,
        job_id=job.id,
        encounter_id=encounter.id,
        audio_id=recording.id,
        wav_path=wav_path,
    )

    return {
        "job_id": job.id,
        "encounter_id": encounter.id,
        "audio_id": recording.id,
        "status": job.status,
        "step": job.step,
        "duration_sec": duration_sec,
    }


@router.get(
    "/dictation-jobs/{job_id}",
    summary="Polling status dan hasil job dikte",
)
def get_dictation_job_status(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Mengambil status pemrosesan dikte (queued, processing, done, error) dan hasil akhir."""
    job = db.get(DictationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan")

    return {
        "id": job.id,
        "encounter_id": job.encounter_id,
        "audio_id": job.audio_id,
        "status": job.status,
        "step": job.step,
        "result": job.result_json,
        "error": job.error,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


@router.get(
    "/dictation/samples",
    summary="Daftar contoh audio dikte klinis untuk demo",
)
def list_dictation_samples(
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Mengambil daftar contoh audio dikte untuk mempermudah pengujian demo sidang."""
    manifest_candidates = [
        Path(get_settings().audio_samples_dir) / "samples.json",
        Path("data/samples/samples.json"),
        Path("backend/data/samples/samples.json"),
    ]
    for p in manifest_candidates:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("Gagal membaca manifest contoh audio: %s", exc)

    return []


@router.post(
    "/encounters/{encounter_id}/dictation/sample/{sample_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Jalankan dikte menggunakan salah satu contoh audio sampel",
)
def run_sample_dictation(
    encounter_id: int,
    sample_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Menjalankan proses dikte langsung dari salah satu file sampel tanpa merekam manual."""
    encounter = db.get(Encounter, encounter_id)
    if not encounter:
        raise AppError(
            status_code=404,
            code="ENCOUNTER_NOT_FOUND",
            detail="Kunjungan tidak ditemukan",
        )

    samples = list_dictation_samples(current_user=current_user)
    selected = next((s for s in samples if s.get("id") == sample_id), None)
    if not selected:
        raise AppError(
            status_code=404,
            code="SAMPLE_NOT_FOUND",
            detail=f"Sampel audio '{sample_id}' tidak ditemukan",
        )

    sample_filename = selected.get("filename")
    samples_dir = Path(get_settings().audio_samples_dir)
    source_audio = samples_dir / str(sample_filename)
    if not source_audio.exists():
        raise AppError(
            status_code=404,
            code="FILE_NOT_FOUND",
            detail=f"File audio sampel {sample_filename} tidak ada di disk",
        )

    # Salin file ke direktori audio encounter
    storage_dir = get_audio_storage_dir()
    safe_name = f"sample_{encounter.id}_{source_audio.name}"
    dest_raw = storage_dir / safe_name
    shutil.copyfile(source_audio, dest_raw)

    dest_wav = storage_dir / f"{dest_raw.stem}_16k.wav"
    convert_to_wav_16k_mono(dest_raw, dest_wav)

    recording = AudioRecording(
        encounter_id=encounter.id,
        file_path=str(dest_raw),
        original_filename=source_audio.name,
        mime_type="audio/wav" if source_audio.suffix == ".wav" else "audio/mpeg",
        duration_sec=selected.get("duration_sec"),
    )
    db.add(recording)
    db.flush()

    job = DictationJob(
        encounter_id=encounter.id,
        audio_id=recording.id,
        status="queued",
        step="stt",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        execute_dictation_job,
        job_id=job.id,
        encounter_id=encounter.id,
        audio_id=recording.id,
        wav_path=str(dest_wav),
    )

    return {
        "job_id": job.id,
        "encounter_id": encounter.id,
        "audio_id": recording.id,
        "status": job.status,
        "step": job.step,
        "duration_sec": selected.get("duration_sec"),
    }


@router.get(
    "/audio/{audio_id}",
    summary="Unduh atau putar audio rekaman",
)
def get_audio_file(
    audio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Mengalirkan file audio rekaman untuk diputar di audio player UI."""
    recording = db.get(AudioRecording, audio_id)
    if not recording or not os.path.exists(recording.file_path):
        raise HTTPException(status_code=404, detail="File audio tidak ditemukan")

    return FileResponse(
        path=recording.file_path,
        media_type=recording.mime_type or "audio/wav",
        filename=recording.original_filename or f"audio_{recording.id}.wav",
    )
