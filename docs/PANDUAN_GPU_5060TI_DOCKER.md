# Panduan Menjalankan Website Demo RME di Komputer dengan GPU RTX 5060 Ti

Panduan ini disiapkan khusus agar Anda dapat dengan mudah memindahkan dan menjalankan proyek ini di komputer lain yang dilengkapi GPU **NVIDIA GeForce RTX 5060 Ti (Arsitektur Blackwell)** menggunakan Docker.

---

## 1. Latar Belakang & Masalah CUDA pada RTX 5060 Ti

GPU seri RTX 50 (Blackwell) menggunakan Compute Capability baru (`sm_100` / `sm_120`). Jika dijalankan di host Windows biasa tanpa CUDA Toolkit & PyTorch yang tepat, Python akan memunculkan error:
```
NVIDIA GeForce RTX 5060 Ti with CUDA capability sm_... is not compatible with the current PyTorch installation.
```
**Solusi Terbaik:** Menjalankan backend di dalam container Docker berbasis image resmi PyTorch CUDA 12.4+ (`pytorch/pytorch:2.4.0-cuda12.4-cudnn9-runtime`), sama persis seperti yang berhasil Anda gunakan saat fine-tuning model Whisper kemarin.

---

## 2. Prasyarat di Komputer GPU (RTX 5060 Ti)

1. **Driver NVIDIA:** Pastikan driver NVIDIA Game Ready / Studio terbaru sudah terpasang di Windows.
2. **Docker Desktop:**
   - Install Docker Desktop for Windows.
   - Buka **Settings -> Resources -> WSL 2 based engine** -> Centang **Use the WSL 2 based engine**.
   - (Secara default, WSL 2 sudah otomatis mendukung NVIDIA GPU Passthrough ke Docker container).

---

## 3. Langkah Pemindahan & Penempatan Bobot Model

1. **Clone / Salin repository** proyek ini ke komputer target.
2. **Salin bobot model Whisper fine-tuned:**
   Letakkan seluruh folder hasil fine-tuning Whisper Anda ke dalam direktori:
   ```
   backend/models_store/whisper/
   ```
   *Pastikan di dalam folder tersebut terdapat file: `config.json`, weights (`model.safetensors` atau `pytorch_model.bin`), serta file tokenizer (`tokenizer.json`, `vocab.json`, dll).*

---

## 4. Langkah Menjalankan dengan Docker Compose

Buka terminal (PowerShell atau Command Prompt) di folder root proyek:

### Langkah 1: Siapkan Environment
```bash
cp .env.example .env
```
*(Bila di PowerShell: `Copy-Item .env.example .env`)*

### Langkah 2: Jalankan Docker Compose dengan Layer GPU
Gunakan file `docker-compose.gpu.yml` yang sudah disiapkan:
```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```
> **Tips Praktis:** Jika ingin langsung mengetik `docker compose up -d --build` tanpa mengetik `-f`, cukup salin file override sekali di awal:
> ```bash
> cp docker-compose.gpu.yml docker-compose.override.yml
> docker compose up -d --build
> ```

### Langkah 3: Migrasi Database & Seed Data Demo
Jalankan perintah ini sekali saja saat database baru pertama kali dibuat:
```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed
```

---

## 5. Verifikasi & Pembuktian GPU Aktif

Untuk melihat apakah Whisper sudah berjalan di GPU RTX 5060 Ti, jalankan:
```bash
docker compose logs -f backend
```
Perhatikan baris output:
```log
INFO: Memuat Whisper STT model dari: /app/models_store/whisper (local_found=True)
INFO: Model Whisper berhasil dimuat di device: cuda:0 [NVIDIA GeForce RTX 5060 Ti] (torch_dtype=torch.float16)
```
Teks di atas membuktikan bahwa model Whisper-medium berjalan di VRAM GPU RTX 5060 Ti dengan akselerasi FP16.

---

## 6. Akses Aplikasi

- **Frontend Website:** `http://localhost:5173`
- **Dokumentasi API (Swagger UI):** `http://localhost:8000/docs`
- **Akun Demo Dokter:** `dr.julio@klinikdemo.id` / `demo123`
- **Akun Demo Admin:** `admin@klinikdemo.id` / `demo123`

---

## 7. Menghentikan Layanan
Jika sudah selesai:
```bash
docker compose down
```
*(Data database di `pgdata` dan audio di `data/audio` akan tetap tersimpan aman).*
