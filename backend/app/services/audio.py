"""Layanan pemrosesan audio untuk Website Demo RME.

Menangani:
1. Validasi ukuran dan tipe file audio
2. Penyimpanan file audio mentah di disk
3. Konversi format audio (WebM / MP3 / M4A / OGG) ke WAV 16 kHz mono (PCM 16-bit)
   menggunakan ffmpeg sesuai spesifikasi Bagian 9 rancangan.
4. Ekstraksi durasi audio.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
import wave
from pathlib import Path
from typing import BinaryIO

from app.core.config import get_settings
from app.core.errors import AppError

logger = logging.getLogger(__name__)

# Format audio yang diizinkan untuk upload
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".aac", ".flac"}
ALLOWED_MIME_PREFIXES = ("audio/", "video/webm")  # Browser MediaRecorder sering mengirim video/webm


def get_audio_storage_dir() -> Path:
    """Mengembalikan direktori penyimpanan audio."""
    settings = get_settings()
    path = Path(settings.audio_upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_ffmpeg_available() -> bool:
    """Memeriksa apakah tool ffmpeg tersedia di PATH sistem."""
    return shutil.which("ffmpeg") is not None


def get_wav_duration(wav_path: str | Path) -> float | None:
    """Mengambil durasi file WAV dalam detik menggunakan modul wave standar Python."""
    try:
        with wave.open(str(wav_path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate > 0:
                return round(frames / float(rate), 2)
    except Exception as exc:
        logger.debug("Tidak dapat membaca durasi dengan wave module: %s", exc)

    # Coba via ffprobe jika tersedia
    if shutil.which("ffprobe"):
        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(wav_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            val = float(result.stdout.strip())
            return round(val, 2)
        except Exception as exc:
            logger.debug("ffprobe error: %s", exc)

    return None


def convert_to_wav_16k_mono(input_path: str | Path, output_path: str | Path) -> str:
    """Konversi file audio apa pun ke WAV 16 kHz 1-channel (mono) PCM 16-bit.

    Perintah: ffmpeg -y -i <input> -ar 16000 -ac 1 -c:a pcm_s16le <output>
    """
    input_str = str(input_path)
    output_str = str(output_path)

    if not os.path.exists(input_str):
        raise FileNotFoundError(f"File audio sumber tidak ditemukan: {input_str}")

    if not is_ffmpeg_available():
        # Jika input sudah berformat .wav dan ffmpeg belum ada di host lokal (non-docker),
        # buat salinan langsung dengan log peringatan
        if input_str.lower().endswith(".wav"):
            logger.warning(
                "ffmpeg tidak ditemukan di host. Menyalin file WAV langsung tanpa resample."
            )
            shutil.copyfile(input_str, output_str)
            return output_str

        raise AppError(
            status_code=500,
            code="FFMPEG_NOT_FOUND",
            detail=(
                "Utilitas 'ffmpeg' tidak ditemukan di sistem. "
                "Jalankan aplikasi via Docker Compose atau install ffmpeg di host."
            ),
        )

    cmd = [
        "ffmpeg",
        "-y",  # Timpa file output jika sudah ada
        "-i",
        input_str,
        "-vn",  # Abaikan video stream bila ada (misal webm video/audio)
        "-ar",
        "16000",  # Sample rate 16 kHz
        "-ac",
        "1",  # 1 channel (mono)
        "-c:a",
        "pcm_s16le",  # Format PCM 16-bit
        output_str,
    ]

    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.debug("ffmpeg berhasil mengonversi audio: %s", process.stderr[-200:])
    except subprocess.CalledProcessError as exc:
        logger.error("ffmpeg conversion error: %s", exc.stderr)
        raise AppError(
            status_code=400,
            code="AUDIO_CONVERSION_FAILED",
            detail=f"Gagal mengonversi file audio: {exc.stderr[:200]}",
        ) from None

    return output_str


def save_uploaded_audio(
    file_obj: BinaryIO,
    filename: str,
    encounter_id: int,
    mime_type: str | None = None,
) -> tuple[str, str, float | None]:
    """Menyimpan file audio upload dan menghasilkan versi WAV 16kHz mono.

    Mengembalikan tuple: (raw_file_path, wav_file_path, duration_sec)
    """
    settings = get_settings()
    storage_dir = get_audio_storage_dir()

    # Ekstensi
    ext = Path(filename).suffix.lower() if filename else ".webm"
    if ext not in ALLOWED_EXTENSIONS:
        raise AppError(
            status_code=400,
            code="UNSUPPORTED_AUDIO_FORMAT",
            detail=f"Format file '{ext}' tidak didukung. Gunakan WAV, MP3, M4A, WebM, atau OGG.",
        )

    timestamp = int(time.time())
    safe_basename = f"enc_{encounter_id}_{timestamp}"
    raw_path = storage_dir / f"{safe_basename}{ext}"
    wav_path = storage_dir / f"{safe_basename}_16k.wav"

    # Simpan raw audio
    max_bytes = settings.max_upload_mb * 1024 * 1024
    total_written = 0
    with open(raw_path, "wb") as f_out:
        while chunk := file_obj.read(1024 * 64):
            total_written += len(chunk)
            if total_written > max_bytes:
                # Bersihkan file parsial
                f_out.close()
                raw_path.unlink(missing_ok=True)
                raise AppError(
                    status_code=413,
                    code="AUDIO_TOO_LARGE",
                    detail=f"Ukuran audio melebihi batas {settings.max_upload_mb} MB.",
                )
            f_out.write(chunk)

    # Konversi ke WAV 16 kHz mono
    convert_to_wav_16k_mono(raw_path, wav_path)

    # Dapatkan durasi
    duration = get_wav_duration(wav_path)

    return str(raw_path), str(wav_path), duration
