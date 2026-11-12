import json
import os
from pathlib import Path
import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
key = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={key}"

sample_file = Path(r"D:\Sekolah\Proyek Akhir\archive\audio_recordings\Clean_Transcripts_ID\CAR0001.txt")
dialogue = sample_file.read_text(encoding="utf-8")

prompt = f"""Kamu adalah pakar medis dan NLP klinis Indonesia.
Tugasmu: Dari transkrip dialog medis berikut, buatlah kalimat-kalimat catatan klinis (catatan rekam medis dokter) dalam Bahasa Indonesia baku yang merefleksikan seluruh temuan penting dari percakapan.

Setiap kalimat harus dianotasi:
1. 'soap': 'S' (Subjective), 'O' (Objective), 'A' (Assessment), atau 'P' (Plan).
2. 'entities': daftar entitas klinis di dalam kalimat tersebut:
   - 'text': teks entitas persis seperti di dalam 'sentence'
   - 'label': salah satu dari 'GEJALA', 'TANDA', 'DIAGNOSIS', 'OBAT', 'TINDAKAN', 'PENUNJANG'
   - 'assertion': 'PRESENT' (positif ada), 'ABSENT' (disangkal / negatif), atau 'POSSIBLE' (suspek / kemungkinan)

Pastikan menyertakan:
- Keluhan utama dan riwayat (S) baik yang afirmatif maupun yang negatif (misal tidak ada batuk, tidak ada demam)
- Temuan fisik atau pemeriksaan (O)
- Kesan diagnosis / diferensial diagnosis dokter (A)
- Rencana terapi / obat / edukasi / rujukan (P)

Keluarkan HANYA JSON array valid sesuai skema:
[
  {{
    "sentence": "Pasien mengeluh nyeri dada sebelah kiri terasa tajam sejak 8 jam lalu.",
    "soap": "S",
    "entities": [
      {{"text": "nyeri dada", "label": "GEJALA", "assertion": "PRESENT"}}
    ]
  }},
  {{
    "sentence": "Keluhan sesak napas dan batuk berdarah disangkal oleh pasien.",
    "soap": "S",
    "entities": [
      {{"text": "sesak napas", "label": "GEJALA", "assertion": "ABSENT"}},
      {{"text": "batuk berdarah", "label": "GEJALA", "assertion": "ABSENT"}}
    ]
  }}
]

Transkrip Percakapan:
{dialogue}
"""

payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
}

resp = httpx.post(url, json=payload, timeout=60.0)
print("Status:", resp.status_code)
if resp.status_code == 200:
    data = json.loads(resp.json()["candidates"][0]["content"]["parts"][0]["text"])
    print(f"Berhasil ekstrak {len(data)} kalimat klinis!")
    print(json.dumps(data[:4], indent=2, ensure_ascii=False))
else:
    print(resp.text)
