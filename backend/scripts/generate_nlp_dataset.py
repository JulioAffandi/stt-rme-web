"""Skrip pembuatan dataset NLP klinis Bahasa Indonesia dari korpus Clean_Transcripts_ID.

Menghasilkan dataset berlabel untuk:
1. Klasifikasi kalimat SOAP (Subjective, Objective, Assessment, Plan)
2. Named Entity Recognition (GEJALA, TANDA, DIAGNOSIS, OBAT, TINDAKAN, PENUNJANG)
3. Deteksi Assertion / Negasi (PRESENT, ABSENT, POSSIBLE)

Mendukung checkpoint per file dan agregasi otomatis ke folder data/nlp_datasets.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nlp_utils import compute_entity_offsets

DEFAULT_SRC_DIR = Path(r"D:\Sekolah\Proyek Akhir\archive\audio_recordings\Clean_Transcripts_ID")
DEFAULT_ANNOTATIONS_DIR = Path(r"D:\Sekolah\Proyek Akhir\archive\audio_recordings\Clean_Annotations_ID")
DEFAULT_DATASET_DIR = PROJECT_ROOT / "data" / "nlp_datasets"

MODEL_NAME = "gemini-3.5-flash-lite"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"

SYSTEM_INSTRUCTION = """Kamu adalah dokter spesialis dan pakar informatika medis Indonesia.
Tugasmu adalah menganalisis transkrip percakapan klinis dokter-pasien dalam Bahasa Indonesia, kemudian membuat catatan rekam medis (clinical notes) lengkap berformat SOAP (Subjective, Objective, Assessment, Plan) dalam Bahasa Indonesia baku.

Bagi catatan ke dalam kalimat-kalimat terpisah (satu kalimat per ide/klausa).
Setiap kalimat WAJIB memiliki anotasi:
1. "soap":
   - "S" (Subjective): Keluhan utama pasien, onset, durasi, faktor pemicu/pereda, riwayat penyakit keluarga/pribadi, kebiasaan, serta keluhan yang DISANGKAL / NEGATIF (misal: 'Pasien menyangkal adanya sesak napas dan demam').
   - "O" (Objective): Temuan pemeriksaan fisik dokter (tanda vital, inspeksi, palpasi perut/dada, mata, kulit, suara napas) yang sesuai dengan temuan klinis kasus.
   - "A" (Assessment): Diagnosis klinis, diagnosis kerja, atau diagnosis banding berdasarkan keluhan tersebut.
   - "P" (Plan): Rencana tata laksana, resep obat (nama obat), edukasi pasien, tindakan medis, dan rujukan/pemeriksaan penunjang (lab/rontgen/EKG).

2. "entities": daftar entitas klinis di dalam kalimat tersebut:
   - "text": kata/frasa entitas yang muncul persis di kalimat
   - "label": "GEJALA" | "TANDA" | "DIAGNOSIS" | "OBAT" | "TINDAKAN" | "PENUNJANG"
   - "assertion": "PRESENT" (ada) | "ABSENT" (disangkal / tidak ada / negatif) | "POSSIBLE" (kemungkinan / suspek)

KETENTUAN KUANTITAS PER PERCAKAPAN:
- Minimal 2-4 kalimat untuk S (wajib sertakan minimal 1 kalimat yang memuat negasi keluhan/disangkal)
- Minimal 1-2 kalimat untuk O
- Minimal 1-2 kalimat untuk A
- Minimal 2-3 kalimat untuk P (memuat obat/tindakan/edukasi)

Format output WAJIB HANYA JSON array:
[
  {
    "sentence": "...",
    "soap": "S" | "O" | "A" | "P",
    "entities": [
      {"text": "...", "label": "...", "assertion": "..."}
    ]
  }
]
"""


def annotate_dialogue(dialogue_text: str, api_key: str, client: httpx.Client, max_retries: int = 5) -> list[dict]:
    url = f"{API_URL}?key={api_key}"
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [
            {
                "parts": [
                    {
                        "text": f"Ekstrak catatan rekam medis SOAP teranotasi dari transkrip berikut:\n\n{dialogue_text}"
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
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
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                result = json.loads(raw_text)
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict) and "notes" in result:
                    return result["notes"]
                raise ValueError(f"Hasil bukan JSON array: {raw_text[:100]}")
            elif resp.status_code == 429:
                print(f" [429 Rate Limit] Menunggu {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                print(f" [HTTP {resp.status_code}] Menunggu {delay}s...")
                time.sleep(delay)
                delay *= 1.5
        except (httpx.TimeoutException, httpx.NetworkError, json.JSONDecodeError) as e:
            print(f" [Error: {type(e).__name__}] Menunggu {delay}s...")
            time.sleep(delay)
            delay *= 1.5

    raise RuntimeError("Gagal menganotasi setelah beberapa kali percobaan.")


def aggregate_datasets(annotations_dir: Path, output_dir: Path) -> dict:
    """Menggabungkan seluruh anotasi per-file menjadi dataset tunggal yang rapi."""
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(list(annotations_dir.glob("*.json")))
    print(f"\nMemproses agregasi dari {len(json_files)} file anotasi...")

    soap_records = []
    ner_records = []

    soap_counts = {"S": 0, "O": 0, "A": 0, "P": 0}
    entity_counts = {}
    assertion_counts = {"PRESENT": 0, "ABSENT": 0, "POSSIBLE": 0}

    for f in json_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                continue
            case_id = f.stem
            for idx, item in enumerate(data):
                sentence = item.get("sentence", "").strip()
                soap = item.get("soap", "S").upper()
                if soap not in soap_counts:
                    soap = "S"
                soap_counts[soap] += 1

                raw_entities = item.get("entities", [])
                computed_entities = compute_entity_offsets(sentence, raw_entities)

                for ent in computed_entities:
                    lbl = ent["label"]
                    entity_counts[lbl] = entity_counts.get(lbl, 0) + 1
                    ass = ent["assertion"]
                    if ass in assertion_counts:
                        assertion_counts[ass] += 1

                # Record SOAP
                soap_records.append({
                    "id": f"{case_id}_{idx+1}",
                    "case_id": case_id,
                    "sentence": sentence,
                    "soap": soap,
                })

                # Record NER & Assertion
                ner_records.append({
                    "id": f"{case_id}_{idx+1}",
                    "case_id": case_id,
                    "sentence": sentence,
                    "soap": soap,
                    "entities": computed_entities,
                })
        except Exception as e:
            print(f"Error membaca {f.name}: {e}")

    # Simpan SOAP JSON & CSV
    soap_json_path = output_dir / "soap_classification.json"
    soap_json_path.write_text(json.dumps(soap_records, indent=2, ensure_ascii=False), encoding="utf-8")

    soap_csv_path = output_dir / "soap_classification.csv"
    with open(soap_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["id", "case_id", "sentence", "soap"])
        writer.writeheader()
        writer.writerows(soap_records)

    # Simpan NER & Assertion JSON
    ner_json_path = output_dir / "ner_assertion.json"
    ner_json_path.write_text(json.dumps(ner_records, indent=2, ensure_ascii=False), encoding="utf-8")

    # Simpan Ringkasan Statistik
    stats = {
        "total_cases": len(json_files),
        "total_sentences": len(soap_records),
        "soap_distribution": soap_counts,
        "entity_distribution": entity_counts,
        "assertion_distribution": assertion_counts,
    }
    stats_path = output_dir / "dataset_statistics.json"
    stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n--- HASIL AGREGASI DATASET ---")
    print(f"Total Kasus Medis: {stats['total_cases']}")
    print(f"Total Kalimat Klinis: {stats['total_sentences']}")
    print("Distribusi SOAP:", soap_counts)
    print("Distribusi Entitas:", entity_counts)
    print("Distribusi Assertion:", assertion_counts)
    print(f"File tersimpan di: {output_dir}")
    print("------------------------------")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Generator Dataset NLP Klinis Indonesia")
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC_DIR, help="Folder transkrip ID")
    parser.add_argument("--dst", type=Path, default=DEFAULT_ANNOTATIONS_DIR, help="Folder anotasi per-file")
    parser.add_argument("--out", type=Path, default=DEFAULT_DATASET_DIR, help="Folder dataset agregasi akhir")
    parser.add_argument("--limit", type=int, default=0, help="Jumlah file maksimal yang diproses (0 = semua)")
    parser.add_argument("--file", type=str, default="", help="Hanya proses 1 file tertentu")
    parser.add_argument("--delay", type=float, default=4.0, help="Jeda antar request API dalam detik")
    parser.add_argument("--aggregate-only", action="store_true", help="Hanya lakukan agregasi data yang sudah ada")
    args = parser.parse_args()

    dst_dir: Path = args.dst
    dst_dir.mkdir(parents=True, exist_ok=True)
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.aggregate_only:
        aggregate_datasets(dst_dir, out_dir)
        return

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY tidak ditemukan di environment atau file .env")
        sys.exit(1)

    src_dir: Path = args.src
    if not src_dir.exists():
        print(f"ERROR: Folder sumber tidak ditemukan: {src_dir}")
        sys.exit(1)

    if args.file:
        files = [src_dir / args.file] if (src_dir / args.file).exists() else []
    else:
        files = sorted(list(src_dir.glob("*.txt")))

    total_files = len(files)
    print(f"Ditemukan {total_files} file transkrip di: {src_dir}")
    print(f"Anotasi per file disimpan ke: {dst_dir}")
    print(f"Model Anotasi: {MODEL_NAME}")
    print("-" * 60)

    processed = 0
    skipped = 0

    with httpx.Client() as client:
        for idx, file_path in enumerate(files, start=1):
            if args.limit > 0 and processed >= args.limit:
                print(f"\nLimit {args.limit} file tercapai.")
                break

            out_file = dst_dir / f"{file_path.stem}.json"
            if out_file.exists() and out_file.stat().st_size > 50:
                print(f"[{idx}/{total_files}] SKIP (sudah dianotasi): {file_path.stem}")
                skipped += 1
                continue

            print(f"[{idx}/{total_files}] Menganotasi {file_path.name}...", end="", flush=True)
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            try:
                start_t = time.time()
                annotations = annotate_dialogue(content, api_key=api_key, client=client)
                out_file.write_text(json.dumps(annotations, indent=2, ensure_ascii=False), encoding="utf-8")
                dur = time.time() - start_t
                print(f" SELESAI ({dur:.1f}s, {len(annotations)} kalimat)")
                processed += 1
            except Exception as e:
                print(f" GAGAL: {e}")

            if idx < total_files:
                time.sleep(args.delay)

    print("-" * 60)
    print(f"Anotasi batch selesai: {processed} file baru dianotasi, {skipped} dilewati.")

    # Lakukan agregasi otomatis
    aggregate_datasets(dst_dir, out_dir)


if __name__ == "__main__":
    main()
