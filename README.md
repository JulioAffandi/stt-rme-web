# Klinik Demo — Website RME berbasis Speech-to-Text & NLP

Website demo **Rekam Medis Elektronik (RME)** untuk sidang Proyek Akhir:
dokter mendiktekan anamnesis secara lisan, pipeline **Speech-to-Text (Whisper fine-tuned)**
dan **NLP (klasifikasi SOAP, NER medis, deteksi negasi/assertion)** mengisi formulir
pemeriksaan secara otomatis — dengan langkah **review klinis** sebelum hasil AI diterapkan.

> Dokumen rancangan lengkap: [`RANCANGAN_WEBSITE_RME_STT_NLP.md`](./RANCANGAN_WEBSITE_RME_STT_NLP.md)
> (kontrak API, skema DB, aturan pemetaan, rencana fase, skenario demo).

## Status Pengerjaan

| Fase | Isi | Status |
|---|---|---|
| 1 — Fondasi | Scaffold, Docker Compose, 14 tabel + Alembic, seed, auth JWT (cookie), layout sidebar/topbar, route guard | Selesai |
| 2 — RME dasar | CRUD pasien (No. RM otomatis), kunjungan, Formulir Pemeriksaan Dokter manual (anamnesa, 12 organ, diagnosa/obat/tindakan + modal pencarian, edukasi), master ICD/obat | Selesai |
| 3 — Dikte + STT | Upload & rekam audio browser, job async, konversi WAV 16 kHz (ffmpeg), integrasi Whisper STT (GPU CUDA/CPU), modal dikte & sampel klinis sidang | Selesai |
| 4 — NLP mock & Review | Klasifikasi SOAP, NER medis kamus, deteksi negasi (ABSENT), pemetaan murni ke form RME, Panel Review Klinis interaktif + penanda visual AI | Selesai |
| 5 — NLP asli | Integrasi model SOAP/NER/assertion (`NLP_ENGINE=real`) saat modul siap | Menunggu Model |
| **6 — Evaluasi & Polish** | **Halaman log pipeline (`/pipeline-logs`), metrik agregat WER/F1/latensi, skrip benchmark offline, Dasbor evaluasi sidang** | **Selesai** |

## Arsitektur

```
frontend (React 19 + Vite + TS + Tailwind v4 + shadcn-style)
   │  proxy /api  (cookie httpOnly JWT)
   ▼
backend (FastAPI + SQLAlchemy 2 + Alembic)
   │
   ▼
db (PostgreSQL 16)  ──  models_store/ (bobot Whisper, Fase 3+)
```

- **Auth:** JWT disimpan sebagai **httpOnly cookie** (`access_token`) + dukungan header
  `Authorization: Bearer` untuk testing. Tidak memakai localStorage.
- **NLP:** dikontrak lewat interface di `backend/app/nlp/` (Bagian 6 rancangan) dan dipilih
  lewat env `NLP_ENGINE=mock|real`. Saat ini `mock` (aturan sederhana) — banner mode demo
  tampil otomatis di UI.
- **Audio:** backend image sudah menyertakan `ffmpeg` (dipakai Fase 3: konversi ke WAV 16 kHz).

## Prasyarat

**Jalur Docker (disarankan untuk demo):**
- Docker Desktop (Windows) dengan **WSL 2 integration** aktif, atau Docker Engine di Linux.

**Jalur manual (tanpa Docker):**
- Node.js ≥ 20 (dites dengan Node 22)
- Python ≥ 3.10 (dites dengan 3.10 & direkomendasikan 3.11 di Docker)
- PostgreSQL ≥ 14 (atau gunakan SQLite untuk coba-coba — lihat Catatan)

## Menjalankan dengan Docker Compose

### A. Mode Standar (CPU / Pengembangan Ringan)

```bash
# 1. Siapkan environment
cp .env.example .env

# 2. Jalankan semua layanan
docker compose up -d --build

# 3. Migrasi database + seed (sekali di awal)
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed
```

### B. Mode GPU (NVIDIA RTX 5060 Ti / Blackwell dengan CUDA 12.4+)

Gunakan file override [`docker-compose.gpu.yml`](./docker-compose.gpu.yml) yang memakai base image resmi PyTorch CUDA (`pytorch/pytorch:2.4.0-cuda12.4-cudnn9-runtime`) dengan passthrough GPU:

```bash
# Jalankan dengan profile GPU
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build

# Atau salin menjadi file override default:
cp docker-compose.gpu.yml docker-compose.override.yml
docker compose up -d --build

# Migrasi + seed
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed
```

*(Di log backend akan tercetak konfirmasi: `Model Whisper berhasil dimuat di device: cuda:0 [NVIDIA GeForce RTX 5060 Ti]`)*

Buka:
- Frontend: http://localhost:5173
- API docs (Swagger): http://localhost:8000/docs
- Postgres: `localhost:5432` (user/db dari `.env`)

## Menjalankan tanpa Docker (pengembangan)

```bash
# --- Backend ---
cd backend
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env                            # isi DATABASE_URL lokal
export DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/rme_stt"
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload --port 8000

# --- Terminal lain: Frontend ---
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxy /api -> localhost:8000)
```

Ubah `VITE_API_PROXY_TARGET` di env bila backend tidak di `localhost:8000`.

## Akun & data demo

Seed (`backend/scripts/seed.py`) membuat:

| Data | Jumlah |
|---|---|
| Akun | 2 |
| Pasien **fiktif** | 8 |
| ICD-10 | ~214 |
| Obat (+harga) | 38 |
| Tindakan (+biaya) | 12 |

| Role | Email | Password |
|---|---|---|
| Dokter | `dr.julio@klinikdemo.id` | `demo123` |
| Admin | `admin@klinikdemo.id` | `demo123` |

> **Privasi:** seluruh data pasien adalah fiktif/sintetis. Jangan pernah memuat data pasien
> nyata. Footer aplikasi mencantumkan "Data demo, bukan data pasien sebenarnya".

## Struktur Repository

```
.
├── docker-compose.yml        # db + backend + frontend
├── .env.example              # template environment (salin ke .env)
├── backend/
│   ├── app/
│   │   ├── api/              # router auth, health (+ deps)
│   │   ├── core/             # config, security (bcrypt+JWT), errors
│   │   ├── db/               # engine, session, Base
│   │   ├── models/           # 14 tabel (gaya FHIR/SATUSEHAT)
│   │   ├── schemas/          # Pydantic
│   │   ├── nlp/              # kontrak engine NLP (Fase 4/5)
│   │   └── services/         # pipeline (Fase 3+)
│   ├── alembic/              # migrasi (versi awal: initial schema)
│   ├── scripts/seed.py       # data demo (idempoten)
│   └── tests/                # pytest
└── frontend/
    ├── src/
    │   ├── components/       # layout (sidebar/topbar/guard), ui, feedback
    │   ├── hooks/            # useAuth (me/login/logout)
    │   ├── lib/              # axios client + helper error
    │   ├── routes/           # halaman
    │   ├── router.tsx        # semua rute (guard + placeholder fase 2+)
    │   └── types/            # tipe TS selaras Pydantic
    └── vite.config.ts        # proxy /api + alias @/
```

## Pengujian

```bash
# Backend (ruff, black, pytest)
cd backend
.venv/bin/ruff check app scripts tests
.venv/bin/black --check app scripts tests
# Tanpa PostgreSQL (pakai SQLite):
TEST_DATABASE_URL=sqlite:///./_test_rme.db pytest
# Dengan PostgreSQL (membuat database *_test):
pytest

# Frontend
cd frontend
npm run lint        # oxlint
npm run format      # prettier
npm run build       # typecheck (tsc -b) + bundling
```

Cakupan test saat ini: health, auth (Fase 1), seed idempoten, serta Fase 2 (`tests/test_rme.py`):
pasien (create/auto No. RM/cari/ubah/duplikat), master search, kunjungan, simpan & baca
pemeriksaan (replace, subtotal, validasi organ/ICD/obat), riwayat kunjungan, dashboard.

> Catatan Fase 2: tombol **Pencatatan Suara** serta aksi Buat Janji/Resep/Surat sengaja nonaktif
> (Fase 3+). Tab *Tanda Tanda Vital* dan *Riwayat Alergi* masih kosong. Form memakai state React
> biasa (RHF/Zod belum dipakai). Endpoint tambahan di luar tabel API rancangan: `GET /dashboard/summary`.

## Kontrak NLP (jangan diubah sembarangan)

Semua modul pipeline (STT, SOAP, NER, assertion) diakses lewat interface di
`backend/app/nlp/base.py` dan dipilih via `NLP_ENGINE`. Format hasil pipeline ke frontend
ada di Bagian 6 dokumen rancangan. **Frontend tidak boleh perlu diubah** ketika engine mock
diganti model asli.

## Catatan Keputusan Desain

1. **JWT via httpOnly cookie** (bukan localStorage) demi keamanan konteks medis; axios
   memakai `withCredentials`, Vite mem-proxy `/api` sehingga cookie same-origin.
2. **Satu sesi Alembic berisi seluruh 14 tabel** (termasuk `audio_recording`,
   `dictation_job`) agar Fase 3 tidak perlu migrasi skema besar.
3. **Frontend berjalan sebagai dev server di Docker** (cukup untuk demo sidang). Bila ingin
   production build, tambahkan stage `npm run build` + static server.
4. **oxlint + Prettier** untuk frontend (template Vite terbaru memakai oxlint; ESLint dapat
   ditambahkan belakangan tanpa mengubah kode).
5. SQLite dipakai **hanya** untuk smoke-test lokal tanpa PostgreSQL; target produksi/demo
   tetap **PostgreSQL 16**.

## Troubleshooting

| Gejala | Solusi |
|---|---|
| `password authentication failed` / koneksi DB gagal | Cek `DATABASE_URL` di `.env`; pastikan `docker compose up -d db` sudah healthy (`docker compose ps`) |
| Port 5432/8000/5173 bentrok | Ubah bagian kiri mapping port di `docker-compose.yml` |
| Frontend `ERR_NETWORK` / CORS | Pastikan backend jalan; `CORS_ORIGINS` di `.env` = `http://localhost:5173` |
| Perubahan model SQLAlchemy tidak muncul | `alembic revision --autogenerate -m "pesan"` lalu `alembic upgrade head` |
| Whisper (Fase 3) belum ada | Wajar — `NLP_ENGINE=mock`; bobot ditaruh di `backend/models_store/whisper/` |

## Cara Menjalankan Model Whisper Fine-Tuned (GPU / CPU)

1. Salin folder hasil fine-tuning Whisper (format Hugging Face `save_pretrained` yang berisi `config.json`, weights `*.safetensors`, dan file tokenizer) ke direktori:
   `backend/models_store/whisper/`
2. Di PC dengan GPU NVIDIA (misal RTX 5060 Ti / arsitektur Blackwell), panduan deployment lengkap dengan Docker CUDA 12.4+ tersedia di:
   👉 **[`docs/PANDUAN_GPU_5060TI_DOCKER.md`](./docs/PANDUAN_GPU_5060TI_DOCKER.md)**
3. Backend akan mendeteksi GPU CUDA secara otomatis (`cuda:0`) dan memuat model sekali saat startup menggunakan Hugging Face ASR pipeline dengan chunking 30 detik.
4. Jika bobot model belum diletakkan di folder lokal, sistem secara otomatis menjalankan mode fallback cerdas (mencocokkan file sampel klinis di `data/samples/` atau skenario Bagian 13) sehingga seluruh antarmuka dan pipeline tetap dapat diuji coba tanpa hambatan.

## Roadmap & Langkah Berikutnya

- [x] **Fase 1: Fondasi Proyek** (Docker, 14 tabel DB, Alembic, seed data, auth JWT cookie, UI layout)
- [x] **Fase 2: RME Manual** (CRUD pasien, kunjungan, form pemeriksaan fisik 12 organ, ICD-10, obat, tindakan, edukasi)
- [x] **Fase 3: Dikte Suara & Whisper STT** (Upload/rekam audio, konversi ffmpeg 16 kHz, async pipeline, modal dikte, audio waveform)
- [x] **Fase 4: Modul NLP Mock & Panel Review Klinis** (SOAP classifier, NER medis, assertion/negasi, mapping murni, ReviewPanel interaktif dengan highlight & toggle)
- [ ] **Fase 5: Integrasi Model NLP Asli** (Mengganti engine mock ke model IndoBERT/XLM-R terlatih via interface `backend/app/nlp/base.py` & env `NLP_ENGINE=real`)
- [x] **Fase 6: Evaluasi, Logging & Dasbor Sidang** (Log pipeline per-tahap, metrik WER/latensi/eksekusi, skrip benchmark offline, halaman `/pipeline-logs`, dashboard ringkasan metrik)
