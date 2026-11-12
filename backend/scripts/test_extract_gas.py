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

prompt = f"""Kamu adalah pakar informatika medis dan NLP klinis Indonesia.
Tugasmu: Dari transkrip dialog medis berikut, buatlah ringkasan catatan klinis (catatan rekam medis dokter) dalam bentuk kalimat-kalimat terpisah dalam Bahasa Indonesia baku yang mencakup keempat komponen SOAP (Subjective, Objective, Assessment, Plan).

Setiap kalimat harus dianotasi:
1. 'soap': 
   - 'S': Keluhan utama pasien, onset, durasi, faktor peringan/pemberat, riwayat penyakit, serta keluhan yang DISANGKAL (negatif).
   - 'O': Temuan pemeriksaan fisik dokter (misal nyeri tekan, bising usus, mata, kulit, tanda vital).
   - 'A': Kesan diagnosis dokter, diagnosis kerja, diagnosis banding, atau kesimpulan sementara.
   - 'P': Rencana terapi dokter, obat yang diresepkan/disarankan, anjuran pemeriksaan penunjang (lab/rontgen), tindakan medis, dan edukasi pasien.
2. 'entities': daftar entitas klinis di dalam kalimat tersebut:
   - 'text': potongan teks entitas persis di dalam kalimat
   - 'label': salah satu dari 'GEJALA', 'TANDA', 'DIAGNOSIS', 'OBAT', 'TINDAKAN', 'PENUNJANG'
   - 'assertion': 'PRESENT' (positif ada), 'ABSENT' (disangkal / negatif), atau 'POSSIBLE' (kemungkinan / suspek)

Pastikan ada perwakilan kalimat untuk kelas S, O, A, dan P jika tercermin dari percakapan!

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
    print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print(resp.text)
