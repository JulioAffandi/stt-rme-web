# Rancangan Website Demo RME berbasis Speech-to-Text & NLP

> Dokumen ini adalah **spesifikasi + instruksi kerja untuk AI coding agent** (Claude Code, Cursor, Copilot, dll.).
> Baca seluruh dokumen sebelum menulis kode. Kerjakan per fase (Bagian 11) dan jangan melompat.

---

## 0. Konteks Proyek

- **Judul PA:** Penerapan Teknologi Speech-to-Text dan Natural Language Processing untuk Otomatisasi Pencatatan Rekam Medis Elektronik.
- **Tujuan website:** Demo yang bisa dilihat dan dicoba oleh penguji/dosen. Website meniru RME sederhana ("Klinik Demo") tempat dokter mendiktekan anamnesis lalu form pemeriksaan terisi otomatis.
- **Status saat ini:**
  - Modul STT (Whisper fine-tuned) **sudah selesai dilatih**.
  - Modul NLP (klasifikasi SOAP, NER, deteksi negasi/assertion) **belum selesai**.
  - Karena itu, website harus dibangun dengan **NLP berupa stub/mock yang bisa diganti** tanpa mengubah frontend (lihat Bagian 6).
- **Bahasa UI:** Bahasa Indonesia. **Bahasa kode/identifier:** Inggris (nama tabel boleh Inggris mengikuti desain FHIR di proposal).

### Pipeline (dari proposal)

```
Audio (WAV 16 kHz) -> STT (Whisper) -> Pra-proses teks -> Klasifikasi SOAP (IndoBERT)
  -> NER medis (IndoBERT/XLM-R, BIO) -> Deteksi negasi/assertion (rule + IndoBERT)
  -> Pemetaan ke DB RME (gaya HL7 FHIR / SATUSEHAT) -> PostgreSQL
```

---

## 1. Keputusan Teknologi

| Lapisan | Pilihan | Alasan |
|---|---|---|
| Frontend | **React 18 + Vite + TypeScript** | SPA ringan, cepat di-build, mudah di-generate agent |
| Styling | **Tailwind CSS + shadcn/ui** | Cocok dengan mockup (sidebar hijau, kartu, tombol berwarna) |
| State/data fetching | **TanStack Query** + **React Hook Form** + **Zod** | Polling job pipeline, validasi form |
| Routing | **React Router v6** | |
| Rekam suara | **MediaRecorder API** (browser) | Tanpa library tambahan; fitur Rekam, Jeda, Berhenti, Upload |
| Backend | **FastAPI (Python 3.11)** | Satu bahasa dengan Whisper/Transformers; sudah ada di Gambar 3.3 proposal |
| ORM & migrasi | **SQLAlchemy 2.0 + Alembic** | |
| Database | **PostgreSQL 16** | Sesuai proposal |
| Auth | **JWT** (python-jose) + bcrypt | Cukup untuk demo, 2 role: `doctor`, `admin` |
| Job async | **FastAPI BackgroundTasks** (fase awal), opsional **Celery + Redis** | Inferensi Whisper lambat, jangan blocking |
| Audio | **ffmpeg** | Konversi webm/opus/mp3/m4a menjadi WAV 16 kHz mono |
| Deploy | **Docker Compose** (`frontend`, `backend`, `db`) | Satu perintah `docker compose up` |

> **Catatan hosting:** Whisper butuh CPU kuat/GPU. Untuk demo sidang, opsi paling aman: jalankan seluruh stack di laptop sendiri lalu ekspos lewat **Cloudflare Tunnel / ngrok** bila perlu diakses penguji. Jangan deploy ke hosting gratis yang tidak sanggup menjalankan model.

> **Opsi alternatif (jika ingin satu codebase):** Next.js full-stack. **Tidak direkomendasikan** karena inferensi model tetap harus di Python, jadi tetap butuh dua service.

---

## 2. Struktur Repository

```
rme-stt-nlp/
├── docker-compose.yml
├── .env.example
├── README.md
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── routes/            # halaman
│   │   ├── components/
│   │   │   ├── layout/        # Sidebar, Topbar
│   │   │   ├── patient/       # PatientCard, PatientForm
│   │   │   ├── exam/          # AnamnesisField, PhysicalExamList, DiagnosisTable, MedicationTable, ProcedureTable
│   │   │   ├── dictation/     # DictationModal, Recorder, UploadDropzone, ReviewPanel, EntityBadge
│   │   │   └── ui/            # shadcn
│   │   ├── lib/               # api client, utils
│   │   ├── hooks/             # useRecorder, useDictationJob
│   │   └── types/             # tipe TS (selaras skema Pydantic)
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/              # config, security
│   │   ├── db/                # session, base
│   │   ├── models/            # SQLAlchemy
│   │   ├── schemas/           # Pydantic
│   │   ├── api/               # router per resource
│   │   ├── services/
│   │   │   ├── audio.py       # ffmpeg convert
│   │   │   ├── pipeline.py    # orkestrasi
│   │   │   └── mapping.py     # hasil NLP -> record RME
│   │   └── nlp/
│   │       ├── base.py        # interface (Protocol)
│   │       ├── stt_whisper.py # IMPLEMENTASI NYATA
│   │       ├── mock.py        # STUB sementara
│   │       └── registry.py    # pilih engine via env
│   ├── alembic/
│   ├── models_store/          # bobot model (gitignore)
│   ├── tests/
│   └── requirements.txt
└── docs/
```

---

## 3. Halaman & Alur Pengguna

Mengacu pada mockup Gambar 3.4–3.7 di proposal.

| Rute | Halaman | Isi |
|---|---|---|
| `/login` | Login | Email + password |
| `/` | Dashboard | Ringkasan: jumlah pasien, kunjungan hari ini, ringkasan metrik pipeline (WER/F1 terakhir dari `pipeline_log`) |
| `/patients` | Data pasien | Tabel + pencarian + tombol tambah |
| `/patients/new` | Pendaftaran pasien baru | Form `patient` |
| `/patients/:id` | Detail pasien | Biodata + riwayat kunjungan |
| `/encounters/:id/exam` | **Formulir Hasil Pemeriksaan Dokter (halaman utama demo)** | Lihat Bagian 4 |
| `/pipeline-logs` | Log & evaluasi pipeline | Tabel `pipeline_log` (WER, SOAP F1, NER F1), cocok untuk ditunjukkan ke penguji |

**Sidebar** (hijau, seperti mockup): Dashboard, Data Master (Obat, Diagnosis ICD), Kunjungan Rawat Jalan -> Pendaftaran Pasien Baru / Pendaftaran Pasien Lama / Pemeriksaan Dokter, Log Pipeline.

---

## 4. Halaman Utama: Formulir Pemeriksaan Dokter

Layout dua kolom:

- **Kiri:** kartu pasien (foto/avatar, Nama, No. RM, Tgl Lahir, Umur) + tombol: Lihat Riwayat Kunjungan, Buat Janji Kunjungan, Buat Resep Dokter, Buat Surat.
- **Kanan:** tab `Pemeriksaan | Tanda Tanda Vital | Riwayat Alergi dan Penyakit`. Tab **Pemeriksaan** berisi:
  1. **Anamnesa** (textarea) + tombol biru **"Pencatatan Suara"** -> membuka modal dikte.
  2. **Pemeriksaan Fisik:** 12 baris organ (Kepala, Mata, Telinga, Leher, Thorax, Paru, Jantung, Abdomen, Inguinal, Ekstremitas Atas, Ekstremitas Bawah, Kulit). Tiap baris = checkbox + input teks. Default input berisi "Normal" dan **disabled**; saat checkbox dicentang, input aktif dan bisa diisi temuan (mis. Mata -> "Mata merah").
  3. **Diagnosa:** tabel (No, Kode ICD, Nama Diagnosa) + tombol Input Diagnosa (modal pencarian ICD-10).
  4. **Obat:** tabel (No, Nama Obat, Dokter, Harga, Jumlah, Subtotal) + Input Obat (modal pencarian master obat).
  5. **Tindakan:** tabel (No, Nama Tindakan, Biaya) + Input Tindakan.
  6. **Edukasi** (textarea).
  7. Tombol **Simpan Hasil Pemeriksaan** (hijau) dan **Kembali** (merah).

### 4.1 Modal "Rekam / Unggah Dikte Medis" (Gambar 3.6–3.7)

State machine:

```
idle ──(Mulai Rekam)──> recording ──(Jeda)──> paused ──(Lanjut)──> recording
  │                         └──(Berhenti)──> uploading
  └──(Upload File)──────────────────────────> uploading
uploading -> processing (polling job) -> review -> (Terapkan ke Form) -> modal tutup
                                   └──> error (tombol Coba Lagi)
```

- `idle`: dropzone "Upload File **atau** Mulai Rekam".
- `recording`/`paused`: timer `mm.ss,cs`, tombol **Jeda** (biru) dan **Berhenti** (merah). Tampilkan visualisasi level suara sederhana.
- `processing`: stepper progres: *Transkripsi -> Klasifikasi SOAP -> Ekstraksi Entitas -> Deteksi Negasi*.
- `review`: lihat 4.2.

### 4.2 Panel Review (PENTING, tambahan dari mockup)

Mockup di proposal langsung mengisi form. **Disarankan menambah langkah review** karena (a) ini konteks klinis, (b) memperlihatkan kerja tiap modul ke penguji, dan (c) sejalan dengan proposal yang menyebut perlunya supervisi klinisi.

Panel review menampilkan:

1. **Transkrip** (dapat diedit) + pemutar audio.
2. **Kalimat berlabel SOAP:** tiap kalimat punya badge `S / O / A / P` (dapat diubah lewat dropdown).
3. **Entitas ter-highlight** inline, warna per jenis (selaras Gambar 3.1: Gejala = kuning, Diagnosis = hijau, Obat = biru; tambah Tanda/Temuan, Tindakan, Penunjang) + ikon status assertion: `PRESENT` (+), `ABSENT` (−), `POSSIBLE` (?). Klik entitas untuk koreksi label/status.
4. **Pratinjau pemetaan:** "Akan mengisi: Anamnesa, Pemeriksaan Fisik (Mata), Diagnosa, Obat...".
5. Tombol **Terapkan ke Form** dan **Batal**.

Setelah "Terapkan", form terisi (seperti Gambar 3.5) dan field yang terisi otomatis diberi **penanda visual** (mis. ikon sparkle/border hijau muda) agar dokter tahu mana yang dari AI dan wajib diverifikasi.

---

## 5. Skema Database

Ikuti Gambar 3.2 (gaya FHIR). Tambahan di bawah diperlukan agar demo berfungsi.

**Tabel dari proposal:** `patient`, `encounter`, `soap_note`, `condition`, `observation`, `procedure`, `medication_request`, `pipeline_log`.

**Tabel tambahan:**

| Tabel | Kolom utama | Fungsi |
|---|---|---|
| `app_user` | id, email, password_hash, full_name, role | Login dokter/admin |
| `icd10_master` | code, name | Pencarian kode diagnosis |
| `drug_master` | id, name, unit, price | Master obat, harga (untuk subtotal) |
| `procedure_master` | id, name, price | Master tindakan, biaya |
| `audio_recording` | id, encounter_id, file_path, duration_sec, created_at | Menyimpan dikte |
| `dictation_job` | id, encounter_id, audio_id, status, result_json, error, created_at | Status & hasil pipeline (untuk polling) |

**Penyesuaian disarankan pada tabel proposal:**

- `observation`: gunakan `soap_section` (`S`/`O`), `observation_type` (`symptom` | `physical_exam` | `vital_sign`), `body_site` (varchar, mis. "Mata", untuk 12 organ), `entity_label`, `assertion_status` (`PRESENT`/`ABSENT`/`POSSIBLE`).
- `condition`: tambahkan `assertion_status` dan `source` (`manual` | `ai`).
- Semua tabel yang bisa terisi AI: tambahkan `source` dan `verified_by_doctor` (bool) agar jejak audit jelas.
- `pipeline_log`: isi `encounter_id`, versi model, `wer_value` (hanya jika ground truth diinput), `soap_f1`, `ner_f1`, plus `latency_ms` per modul.

> Catatan: `wer_value`/`f1` per kunjungan hanya ada jika ada ground truth. Siapkan juga **halaman/skrip evaluasi offline** (di luar alur dokter) yang menjalankan test set dan menulis ke `pipeline_log` untuk data di bab Eksperimen.

---

## 6. Kontrak NLP (kunci agar bisa dibangun sebelum model NLP selesai)

Semua modul pipeline diakses lewat **interface**. Implementasi dipilih via env `NLP_ENGINE=mock|real`.

```python
# backend/app/nlp/base.py
from typing import Protocol
from pydantic import BaseModel

class Segment(BaseModel):
    start: float | None = None
    end: float | None = None
    text: str

class SttEngine(Protocol):
    def transcribe(self, wav_path: str) -> list[Segment]: ...

class SoapClassifier(Protocol):
    def classify(self, sentences: list[str]) -> list[str]: ...   # "S"|"O"|"A"|"P"

class Entity(BaseModel):
    text: str
    label: str            # GEJALA|TANDA|DIAGNOSIS|OBAT|TINDAKAN|PENUNJANG
    start: int            # offset karakter pada kalimat
    end: int
    sentence_idx: int

class NerEngine(Protocol):
    def extract(self, sentences: list[str]) -> list[Entity]: ...

class AssertionEngine(Protocol):
    def classify(self, sentences: list[str], entities: list[Entity]) -> list[str]:
        ...   # "PRESENT"|"ABSENT"|"POSSIBLE", sejajar dengan entities
```

### Format hasil pipeline (kontrak API ke frontend, jangan diubah sembarangan)

```json
{
  "transcript": "Pasien mengeluh pusing dan muntah. Tidak ada sesak napas. Mata merah. ...",
  "sentences": [
    { "idx": 0, "text": "Pasien mengeluh pusing dan muntah.", "soap": "S" }
  ],
  "entities": [
    { "text": "pusing", "label": "GEJALA", "start": 17, "end": 23,
      "sentence_idx": 0, "assertion": "PRESENT" }
  ],
  "timings_ms": { "stt": 0, "soap": 0, "ner": 0, "assertion": 0 }
}
```

### Implementasi

- `stt_whisper.py` — **real sejak awal**: muat model hasil fine-tuning dari `models_store/whisper/` (HF Transformers `pipeline("automatic-speech-recognition")`; bila ingin lebih cepat, boleh konversi ke faster-whisper/CTranslate2 **hanya jika** hasil WER terverifikasi sama). Muat model **sekali** saat startup (singleton), bukan per request. Audio panjang -> chunking (`chunk_length_s=30`).
- `mock.py` — **stub sementara** untuk SOAP/NER/Assertion:
  - SOAP: aturan kata kunci (mis. "mengeluh/riwayat" -> S; "tampak/tekanan darah/pemeriksaan" -> O; "diagnosis/kesan" -> A; "diberikan/resep/anjuran/kontrol" -> P).
  - NER: pencocokan kamus kecil (gejala, diagnosis, obat) dari master data.
  - Assertion: rule negasi ("tidak ada", "tidak ditemukan", "tidak tampak", "belum tampak", "tanpa", "bukan").
  - Beri banner di UI saat `NLP_ENGINE=mock`: **"Mode demo: modul NLP menggunakan aturan sederhana"**.
- Saat model NLP asli selesai: buat `soap_indobert.py`, `ner_transformer.py`, `assertion_hybrid.py` yang memenuhi interface yang sama, lalu ganti env. **Frontend tidak boleh perlu diubah.**

---

## 7. Aturan Pemetaan Hasil NLP ke Form/DB (`services/mapping.py`)

Fungsi **murni** (tanpa I/O) agar mudah diuji.

| SOAP | Entitas | Assertion | Target form | Target tabel |
|---|---|---|---|---|
| S | GEJALA | PRESENT | Anamnesa: tambahkan teks keluhan | `observation` (type=`symptom`), `soap_note.subjective_text` |
| S | GEJALA | ABSENT | Anamnesa: tulis "Tidak ada {gejala}" | `observation` dengan `assertion_status=ABSENT` |
| S | GEJALA | POSSIBLE | Anamnesa: "Kemungkinan {gejala}" | `observation` POSSIBLE |
| O | TANDA/TEMUAN | PRESENT | Pemeriksaan Fisik: centang organ + isi temuan | `observation` (type=`physical_exam`, `body_site`) |
| O | TANDA/TEMUAN | ABSENT | Organ tetap/dikembalikan "Normal" (jangan dicentang) | tetap disimpan dengan ABSENT |
| A | DIAGNOSIS | PRESENT | Tabel Diagnosa (cari kode ICD-10 via fuzzy match) | `condition` |
| A | DIAGNOSIS | ABSENT | **Jangan** masuk tabel Diagnosa | `condition` ABSENT (opsional) |
| P | OBAT | PRESENT | Tabel Obat (cocokkan `drug_master`) | `medication_request` |
| P | TINDAKAN | PRESENT | Tabel Tindakan | `procedure` |
| P | (kalimat edukasi) | — | Kolom Edukasi | `soap_note.plan_text` |

Aturan tambahan:

- Kalimat berlabel S/O/A/P selalu disimpan utuh ke `soap_note` (`subjective_text`, `objective_text`, `assessment_text`, `plan_text`).
- **Pencocokan organ:** sinonim ("mata", "konjungtiva" -> Mata; "paru", "pulmo" -> Paru; "abdomen", "perut" -> Abdomen; dst.). Simpan kamus di `mapping.py`.
- **Pencocokan ICD/obat:** exact match dulu, lalu fuzzy (rapidfuzz, ambang >= 85). Bila tidak ada kecocokan -> **jangan menebak**; tampilkan sebagai "perlu dipilih manual" di panel review.
- Entitas ber-status ABSENT **tidak boleh** pernah mengisi data positif (diagnosis/obat/gejala aktif). Ini harus ada unit test.
- Data hasil AI selalu `source='ai'`, `verified_by_doctor=false` sampai dokter menekan Simpan.

---

## 8. Desain API (REST, prefix `/api/v1`)

| Method | Path | Keterangan |
|---|---|---|
| POST | `/auth/login` | -> `{access_token}` |
| GET | `/auth/me` | profil user |
| GET/POST | `/patients` | list (`?q=`) / buat |
| GET/PUT | `/patients/{id}` | detail / ubah |
| GET | `/patients/{id}/encounters` | riwayat kunjungan |
| POST | `/encounters` | buat kunjungan (`patient_id`, `practitioner_id`) |
| GET | `/encounters/{id}` | data kunjungan + semua data klinis |
| POST | `/encounters/{id}/dictation` | multipart `audio` -> `{job_id}` (202) |
| GET | `/dictation-jobs/{job_id}` | `{status: queued\|processing\|done\|error, step, result?}` |
| POST | `/encounters/{id}/exam` | simpan form final (payload di bawah) |
| GET | `/icd10?q=` | pencarian ICD |
| GET | `/drugs?q=` | pencarian obat |
| GET | `/procedures?q=` | pencarian tindakan |
| GET | `/pipeline-logs` | log & metrik |
| POST | `/evaluation/run` | (admin) jalankan evaluasi test set -> tulis `pipeline_log` |
| GET | `/health` | cek status + `NLP_ENGINE` aktif |

Payload simpan form:

```json
{
  "anamnesis": "Pusing, badan menggigil, muntah",
  "physical_exam": [{ "body_site": "Mata", "finding": "Mata merah" }],
  "diagnoses": [{ "icd_code": "A91", "name": "Demam Berdarah", "source": "ai" }],
  "medications": [{ "drug_id": 1, "quantity": 12, "source": "ai" }],
  "procedures": [{ "procedure_id": 3, "source": "manual" }],
  "education": "Perbanyak minum air putih"
}
```

Aturan API: validasi dengan Pydantic, response error seragam `{ "detail": "...", "code": "..." }`, CORS hanya untuk origin frontend, batas ukuran upload (mis. 50 MB) dan tipe file (wav, mp3, m4a, webm, ogg).

---

## 9. Detail Implementasi Penting

**Audio**
- Browser merekam `audio/webm;codecs=opus`. Backend wajib mengonversi ke **WAV 16 kHz mono** dengan ffmpeg sebelum masuk Whisper: `ffmpeg -i in -ar 16000 -ac 1 out.wav`.
- Jangan percayai ekstensi file; validasi dengan ffprobe.
- Simpan audio asli dan WAV hasil konversi di volume `./data/audio/`.

**Job async**
- Endpoint dikte mengembalikan `202` + `job_id` segera. Pipeline berjalan di background; update `dictation_job.status` dan `step` per tahap.
- Frontend polling tiap 1,5 detik via TanStack Query (`refetchInterval`) hingga `done`/`error`.
- Hanya **satu inferensi Whisper berjalan pada satu waktu** (semaphore/antrian) agar tidak kehabisan memori.

**Frontend**
- Hook `useRecorder`: kontrol `start/pause/resume/stop`, timer, error izin mikrofon (tampilkan pesan ramah bila ditolak). Catatan: `getUserMedia` butuh **HTTPS atau localhost**.
- Highlight entitas: render kalimat dengan memotong teks berdasarkan `start/end`, bukan `dangerouslySetInnerHTML`.
- Tipe TypeScript di `types/` harus mencerminkan skema Pydantic (boleh generate dari OpenAPI dengan `openapi-typescript`).
- Aksesibilitas dasar: label form, fokus modal, kontras warna.

**Keamanan & privasi (wajib untuk konteks medis, walau demo)**
- Hanya data **pasien fiktif/sintetis**. Jangan memuat data pasien nyata. Cantumkan footer "Data demo, bukan data pasien sebenarnya".
- Password di-hash (bcrypt), JWT kedaluwarsa singkat, secret lewat `.env` (jangan commit).
- Tidak ada audio atau teks yang dikirim ke layanan cloud pihak ketiga (alasan Whisper lokal dipilih di Tabel 2.1 proposal).
- Foto pasien di mockup hanya placeholder; gunakan avatar inisial.

---

## 10. Data Seed untuk Demo

Siapkan skrip `backend/scripts/seed.py`:
- 1 akun dokter (`dr. Julio`) dan 1 admin.
- 5–10 pasien fiktif.
- ~100 baris `icd10_master` yang sering dipakai (DBD, gastroenteritis akut, ISPA, hipertensi, DM tipe 2, dll.).
- ~30 obat umum (Paracetamol, Amoksisilin, ORS, Omeprazol, dst.) dengan harga.
- ~10 tindakan (Rawat Inap, Injeksi, Nebulisasi, dll.).
- 3–5 file audio contoh + transkrip referensi di `data/samples/` untuk tombol **"Coba dengan contoh dikte"** (memudahkan penguji yang tidak mau merekam).

---

## 11. Rencana Pengerjaan (Fase)

Kerjakan berurutan. Setiap fase harus berjalan (`docker compose up`) sebelum lanjut.

**Fase 1: Fondasi**
1. Scaffold monorepo, `docker-compose.yml` (db, backend, frontend), `.env.example`.
2. Model SQLAlchemy + migrasi Alembic sesuai Bagian 5; skrip seed.
3. Auth (login, `/auth/me`) + layout frontend (sidebar, topbar, route guard).

**Fase 2: RME dasar tanpa AI**
4. CRUD pasien, buat kunjungan, halaman daftar & detail pasien.
5. Halaman Formulir Pemeriksaan **lengkap secara manual** (Anamnesa, 12 organ, Diagnosa/Obat/Tindakan dengan modal pencarian, Edukasi) + endpoint simpan. Hasil harus identik secara visual dengan Gambar 3.4–3.5.

**Fase 3: Dikte + STT nyata**
6. `audio.py` (ffmpeg), endpoint dikte + `dictation_job`, polling.
7. Integrasi `stt_whisper.py` dengan model fine-tuned. Tampilkan transkrip.
8. Modal rekam/unggah (Gambar 3.6–3.7), hook `useRecorder`.

**Fase 4: NLP dengan engine mock**
9. Interface Bagian 6 + `mock.py`, `pipeline.py` orkestrasi, `mapping.py` + unit test.
10. Panel Review (Bagian 4.2) + tombol Terapkan ke Form + penanda field AI.

**Fase 5: Integrasi NLP asli** (saat model siap)
11. Implementasi engine asli per modul, ganti `NLP_ENGINE=real`. Catat versi model di `pipeline_log`.

**Fase 6: Evaluasi & polish**
12. Halaman `/pipeline-logs`, skrip evaluasi offline (WER via `jiwer`; F1 via `seqeval`/`scikit-learn`), Dashboard metrik.
13. Tombol contoh dikte, README, skenario demo (Bagian 13), uji ujung ke ujung.

---

## 12. Instruksi untuk AI Agent

**Aturan umum**
1. Kerjakan **satu fase per sesi**. Di akhir fase, jalankan aplikasi dan tes, lalu ringkas apa yang dibuat dan apa yang belum.
2. **Jangan mengubah** kontrak di Bagian 6 (interface & format JSON) tanpa persetujuan pengguna.
3. **Jangan menggunakan localStorage untuk token jika bisa dihindari**; gunakan memori + httpOnly cookie atau simpan token dengan hati-hati dan catat keputusannya di README.
4. **Jangan mengarang model, bobot, atau metrik.** Bila model asli tidak tersedia, gunakan engine mock dan tampilkan banner mode demo. Nilai WER/F1 hanya boleh berasal dari hasil evaluasi nyata.
5. Jika ada hal yang ambigu (mis. format label dataset, path bobot Whisper), **tanyakan ke pengguna**, jangan menebak.
6. Pertahankan tampilan sesuai mockup: warna dominan hijau (`emerald`/`#059669`), tombol biru untuk aksi AI/tambah, merah untuk kembali/berhenti, oranye/cyan/kuning untuk aksi pasien.

**Kualitas kode**
- Python: type hints, `ruff` + `black`, fungsi pemetaan murni, `pytest`.
- TypeScript: `strict: true`, ESLint + Prettier, tanpa `any`.
- Komponen kecil dan reusable; tidak ada logika bisnis pemetaan di komponen React (semua di backend `mapping.py`).
- Tangani semua state: loading, kosong ("Belum ada data"), error.
- Commit kecil dengan pesan jelas (`feat:`, `fix:`, `chore:`).

**Pengujian minimum**
- Unit test `mapping.py`: kasus PRESENT, ABSENT, POSSIBLE; entitas ABSENT tidak pernah menjadi diagnosis/obat aktif; organ tak dikenal; ICD tidak ditemukan.
- Unit test aturan negasi pada `mock.py` ("tidak ada sesak napas" -> ABSENT).
- Test API: login, buat pasien, upload dikte -> job selesai (dengan engine mock + audio contoh).
- Test e2e manual mengikuti skenario Bagian 13.

**Definisi selesai (Definition of Done) per fitur**
- Berjalan lewat `docker compose up` tanpa langkah manual tersembunyi.
- Ada test relevan yang lolos.
- Tidak ada secret di repo.
- README diperbarui bila ada env/perintah baru.

---

## 13. Skenario Demo (untuk sidang)

1. Login sebagai dokter -> Pemeriksaan Dokter -> pilih pasien demo.
2. Klik **Pencatatan Suara** -> **Mulai Rekam** (atau "Coba dengan contoh dikte"), ucapkan:
   > "Pasien mengeluh pusing, badan menggigil, dan muntah sejak dua hari. Tidak ada sesak napas. Pada pemeriksaan mata tampak merah. Kesan demam berdarah. Diberikan paracetamol, dan dianjurkan banyak minum air putih."
3. Tunjukkan proses: transkripsi -> SOAP -> entitas -> negasi.
4. Di panel review: tunjukkan "sesak napas" berstatus **ABSENT** dan tidak masuk sebagai gejala aktif.
5. **Terapkan ke Form** -> form terisi seperti Gambar 3.5 (Anamnesa, Mata merah, Demam Berdarah + ICD, Paracetamol, Edukasi).
6. Simpan -> buka `/pipeline-logs` untuk menunjukkan WER, SOAP F1, NER F1.

---

## 14. Pertanyaan Terbuka (jawab sebelum Fase 3 dan 5)

- Format & lokasi bobot Whisper hasil fine-tune (HF `save_pretrained`? ukuran model: tiny/base/small/medium?).
- Apakah demo berjalan di mesin dengan GPU? Jika tidak, tentukan ukuran model/quantization yang masih responsif.
- Skema label dataset SOAP/NER/assertion yang final (nama kelas harus sama dengan `Entity.label` di Bagian 6).
- Apakah dikte akan dibatasi durasi maksimum (disarankan 5 menit untuk demo)?
- Apakah perlu bahasa Inggris pada UI? (default: tidak).
