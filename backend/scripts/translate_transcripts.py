"""Skrip penerjemah otomatis korpus dialog klinis (ACI-BENCH) ke Bahasa Indonesia.

Menggunakan Gemini API (model: gemini-3.5-flash-lite) dengan penanganan istilah
medis klinis, format pembicara D:/P:, rate limiting otomatis, serta fitur resume
(melewati file yang sudah selesai diterjemahkan).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load .env dari root stt-whisper-web jika ada
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_SRC_DIR = Path(r"D:\Sekolah\Proyek Akhir\archive\audio_recordings\Clean_Transcripts")
DEFAULT_DST_DIR = Path(r"D:\Sekolah\Proyek Akhir\archive\audio_recordings\Clean_Transcripts_ID")
MODEL_NAME = "gemini-3.5-flash-lite"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"

SYSTEM_INSTRUCTION = """Kamu adalah penerjemah ahli bidang medis yang bertugas menerjemahkan transkrip percakapan klinis dokter dan pasien dari bahasa Inggris ke Bahasa Indonesia yang alami, baku, dan lazim digunakan di fasilitas kesehatan di Indonesia.

ATURAN WAJIB:
1. Pertahankan persis format pembicara di setiap baris, yaitu 'D:' untuk Dokter dan 'P:' untuk Pasien.
2. Terjemahkan istilah medis ke padanan klinis Indonesia yang lazim digunakan dokter/tenaga medis (contoh:
   - 'chest pain' -> 'nyeri dada'
   - 'shortness of breath' -> 'sesak napas'
   - 'heart attack' -> 'serangan jantung'
   - 'high blood pressure' / 'hypertension' -> 'tekanan darah tinggi' atau 'hipertensi'
   - 'nausea' -> 'mual'
   - 'rash' -> 'ruam'
   - 'joint pain' -> 'nyeri sendi'
   - nama obat generik pertahankan ejaan Indonesia/internasional yang lazim).
3. Gunakan gaya tutur yang sopan dan natural sesuai etika komunikasi dokter-pasien di Indonesia.
4. JANGAN menambahkan catatan pembuka, penutup, atau tanda kurung penjelasan. Keluarkan HANYA teks transkrip percakapan hasil terjemahan.
"""


def translate_text(text: str, api_key: str, client: httpx.Client, max_retries: int = 5) -> str:
    url = f"{API_URL}?key={api_key}"
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [
            {
                "parts": [
                    {
                        "text": f"Terjemahkan dialog percakapan klinis berikut ke Bahasa Indonesia sesuai aturan:\n\n{text}"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 8192,
        },
    }

    delay = 5.0
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.post(url, json=payload, timeout=60.0)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
                raise RuntimeError(f"Format respon API kosong atau tidak terduga: {data}")
            elif resp.status_code == 429:
                print(f" [Rate limit 429] Percobaan {attempt}/{max_retries}. Menunggu {delay} detik...")
                time.sleep(delay)
                delay *= 2
            else:
                err_text = resp.text[:200]
                print(f" [HTTP {resp.status_code}] {err_text}. Percobaan {attempt}/{max_retries}...")
                time.sleep(delay)
                delay *= 1.5
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            print(f" [Koneksi Error: {type(e).__name__}] Percobaan {attempt}/{max_retries}. Menunggu {delay} detik...")
            time.sleep(delay)
            delay *= 1.5

    raise RuntimeError("Gagal menerjemahkan setelah beberapa kali percobaan.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Penerjemah Transkrip Medis via Gemini API")
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC_DIR, help="Folder sumber transkrip EN")
    parser.add_argument("--dst", type=Path, default=DEFAULT_DST_DIR, help="Folder tujuan transkrip ID")
    parser.add_argument("--limit", type=int, default=0, help="Jumlah file maksimal yang diproses (0 = semua)")
    parser.add_argument("--file", type=str, default="", help="Hanya proses 1 file tertentu (contoh: CAR0001.txt)")
    parser.add_argument("--delay", type=float, default=4.0, help="Jeda antar request dalam detik (default: 4.0s)")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY tidak ditemukan di environment atau file .env")
        sys.exit(1)

    src_dir: Path = args.src
    dst_dir: Path = args.dst

    if not src_dir.exists():
        print(f"ERROR: Folder sumber tidak ditemukan: {src_dir}")
        sys.exit(1)

    dst_dir.mkdir(parents=True, exist_ok=True)

    if args.file:
        files = [src_dir / args.file] if (src_dir / args.file).exists() else []
        if not files:
            print(f"ERROR: File {args.file} tidak ditemukan di {src_dir}")
            sys.exit(1)
    else:
        files = sorted(list(src_dir.glob("*.txt")))

    total_files = len(files)
    print(f"Ditemukan {total_files} file transkrip di: {src_dir}")
    print(f"Output disimpan ke: {dst_dir}")
    print(f"Model: {MODEL_NAME}")
    print("-" * 60)

    processed = 0
    skipped = 0

    with httpx.Client() as client:
        for idx, file_path in enumerate(files, start=1):
            if args.limit > 0 and processed >= args.limit:
                print(f"\nLimit {args.limit} file tercapai. Selesai.")
                break

            out_file = dst_dir / file_path.name
            if out_file.exists() and out_file.stat().st_size > 100:
                print(f"[{idx}/{total_files}] SKIP (sudah ada): {file_path.name}")
                skipped += 1
                continue

            print(f"[{idx}/{total_files}] Menerjemahkan {file_path.name} ({file_path.stat().st_size} bytes)...", end="", flush=True)
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            try:
                start_t = time.time()
                translated = translate_text(content, api_key=api_key, client=client)
                out_file.write_text(translated, encoding="utf-8")
                dur = time.time() - start_t
                print(f" SELESAI ({dur:.1f}s, {len(translated)} karakter)")
                processed += 1
            except Exception as e:
                print(f" GAGAL: {e}")

            if idx < total_files:
                time.sleep(args.delay)

    print("-" * 60)
    print(f"Rangkuman: {processed} file baru berhasil diterjemahkan, {skipped} dilewati.")


if __name__ == "__main__":
    main()
