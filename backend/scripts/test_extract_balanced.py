import json
import os
from pathlib import Path
import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
key = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={key}"

sample_file = Path(r"D:\Sekolah\Proyek Akhir\archive\audio_recordings\Clean_Transcripts_ID\GAS0001.txt")
dialogue = sample_file.read_text(encoding="utf-8")

prompt = f"""Kamu adalah dokter spesialis dan pakar informatika medis Indonesia.
Dari transkrip percakapan klinis berikut, buatlah catatan rekam medis (clinical notes) lengkap berformat SOAP (Subjective, Objective, Assessment, Plan) dalam Bahasa Indonesia medis baku.

Bagi catatan menjadi kalimat-kalimat tersendiri (1 ide/klausa per kalimat).
Setiap kalimat harus memiliki label:
1. "soap":
   - "S" (Subjective): Keluhan utama pasien, riwayat penyakit, onset/durasi, serta gejala yang dinyatakan tidak ada / disangkal (negasi).
   - "O" (Objective): Temuan pemeriksaan fisik dokter yang relevan dengan keluhan di dialog (tanda vital, inspeksi, palpasi abdomen/organ, dsb).
   - "A" (Assessment): Diagnosis klinis, diagnosis kerja, atau diagnosis banding berdasarkan keluhan tersebut.
   - "P" (Plan): Rencana tata laksana, terapi obat (nama obat), edukasi pasien, dan anjuran pemeriksaan penunjang (lab/USG/tes kehamilan).

2. "entities": daftar entitas medis di dalam kalimat:
   - "text": string kata/frasa entitas yang muncul persis di kalimat
   - "label": "GEJALA" | "TANDA" | "DIAGNOSIS" | "OBAT" | "TINDAKAN" | "PENUNJANG"
   - "assertion": "PRESENT" (ada) | "ABSENT" (tidak ada / disangkal) | "POSSIBLE" (kemungkinan / suspek)

PASTIKAN:
- Minimal ada 2-3 kalimat untuk S (termasuk minimal 1 kalimat negasi keluhan)
- Minimal ada 1-2 kalimat untuk O
- Minimal ada 1 kalimat untuk A
- Minimal ada 2 kalimat untuk P (obat / edukasi / rencana tindakan)

Keluarkan HANYA JSON array valid:
[
  {{
    "sentence": "...",
    "soap": "S" | "O" | "A" | "P",
    "entities": [
      {{"text": "...", "label": "...", "assertion": "..."}}
    ]
  }}
]

Transkrip:
{dialogue}
"""

payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
}

resp = httpx.post(url, json=payload, timeout=60.0)
if resp.status_code == 200:
    data = json.loads(resp.json()["candidates"][0]["content"]["parts"][0]["text"])
    print(f"Berhasil ekstrak {len(data)} kalimat klinis!")
    soaps = {}
    for d in data:
        soaps[d["soap"]] = soaps.get(d["soap"], 0) + 1
    print("Distribusi SOAP:", soaps)
    for d in data:
        print(f"[{d['soap']}] {d['sentence']}")
        for ent in d.get("entities", []):
            print(f"   -> {ent['text']} ({ent['label']}, {ent['assertion']})")
else:
    print(resp.text)
