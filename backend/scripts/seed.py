"""Seed data demo untuk Klinik Demo.

Jalankan dari direktori backend:
    python -m scripts.seed

Idempoten: aman dijalankan berkali-kali (hanya menambah data yang belum ada).
HANYA gunakan data pasien FIKTIF/SINTETIS.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.core.security import hash_password
from app.db.session import get_session_factory
from app.models import (
    DrugMaster,
    Icd10Master,
    Patient,
    PipelineLog,
    ProcedureMaster,
    User,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

# ------------------------------------------------------------------------------
# Akun demo (password di-hash saat runtime — jangan commit hash hasil generate)
# ------------------------------------------------------------------------------
DEMO_PASSWORD = "demo123"

USERS = [
    {
        "email": "dr.julio@klinikdemo.id",
        "full_name": "dr. Julio",
        "role": "doctor",
    },
    {
        "email": "admin@klinikdemo.id",
        "full_name": "Admin Klinik",
        "role": "admin",
    },
]

# ------------------------------------------------------------------------------
# Pasien fiktif (BUKAN data pasien nyata)
# ------------------------------------------------------------------------------
PATIENTS = [
    ("RM-2026-0001", "Siti Aminah", date(1985, 3, 12), "F", "Jl. Melati No. 12", "081234567801"),
    ("RM-2026-0002", "Budi Santoso", date(1978, 7, 25), "M", "Jl. Kenanga No. 5", "081234567802"),
    ("RM-2026-0003", "Citra Lestari", date(1995, 11, 2), "F", "Jl. Anggrek No. 8", "081234567803"),
    ("RM-2026-0004", "Dewi Anggraini", date(2001, 1, 18), "F", "Jl. Dahlia No. 3", "081234567804"),
    ("RM-2026-0005", "Eko Prasetyo", date(1966, 5, 30), "M", "Jl. Mawar No. 21", "081234567805"),
    (
        "RM-2026-0006",
        "Fitri Handayani",
        date(1990, 9, 9),
        "F",
        "Jl. Cempaka No. 17",
        "081234567806",
    ),
    (
        "RM-2026-0007",
        "Gunawan Saputra",
        date(1958, 12, 4),
        "M",
        "Jl. Flamboyan No. 2",
        "081234567807",
    ),
    (
        "RM-2026-0008",
        "Hesti Wulandari",
        date(2010, 6, 21),
        "F",
        "Jl. Bougenville No. 9",
        "081234567808",
    ),
]

# ------------------------------------------------------------------------------
# Master ICD-10 (sering dipakai di klinik) — nama dalam Bahasa Indonesia
# ------------------------------------------------------------------------------
ICD10 = [
    ("A01.0", "Demam tifoid"),
    ("A01.2", "Demam paratifoid B"),
    ("A04.9", "Infeksi bakteri saluran cerna, tak spesifik"),
    ("A05.9", "Keracunan makanan bakteri, tak spesifik"),
    ("A08.4", "Infeksi saluran cerna oleh virus"),
    ("A09", "Diare dan gastroenteritis infeksius, tak spesifik"),
    ("A41.9", "Sepsis, organisme tak spesifik"),
    ("A46", "Erisipelas"),
    ("A49.9", "Infeksi bakteri, tak spesifik"),
    ("A50.9", "Sifilis bawaan, tak spesifik"),
    ("A53.9", "Sifilis, tak spesifik"),
    ("A69.2", "Penyakit Lyme"),
    ("B00.9", "Infeksi virus herpes, tak spesifik"),
    ("B02.9", "Zoster tanpa komplikasi"),
    ("B08.1", "Molluscum contagiosum"),
    ("B15", "Hepatitis akut A"),
    ("B16", "Hepatitis akut B"),
    ("B18.1", "Hepatitis B kronis"),
    ("B18.2", "Hepatitis C kronis"),
    ("B34.9", "Infeksi virus, tak spesifik"),
    ("B35.9", "Dermatofitosis, tak spesifik"),
    ("B36.9", "Infeksi superfisial, tak spesifik"),
    ("B37.9", "Kandidiasis, tak spesifik"),
    ("B54", "Malaria, tak spesifik"),
    ("D50.9", "Anemia defisiensi besi, tak spesifik"),
    ("D64.9", "Anemia, tak spesifik"),
    ("D69.0", "Purpura alergik"),
    ("D69.6", "Trombositopenia, tak spesifik"),
    ("E03.9", "Hipotiroidisme, tak spesifik"),
    ("E05.9", "Tirotoksikosis, tak spesifik"),
    ("E10.9", "Diabetes melitus tipe 1 tanpa komplikasi"),
    ("E11.9", "Diabetes melitus tipe 2 tanpa komplikasi"),
    ("E14.9", "Diabetes melitus, tak spesifik"),
    ("E46", "Malnutrisi protein-kalori, tak spesifik"),
    ("E66.9", "Obesitas, tak spesifik"),
    ("E78.0", "Hiperkolesterolemia"),
    ("E78.5", "Hiperlipidemia, tak spesifik"),
    ("E87.6", "Hipokalemia"),
    ("E87.1", "Hiponatremia"),
    ("F10.2", "Ketergantungan alkohol"),
    ("F32.9", "Depresi mayor, episode tunggal, tak spesifik"),
    ("F33.9", "Gangguan depresif berulang, tak spesifik"),
    ("F41.0", "Gangguan panik"),
    ("F41.1", "Gangguan cemas umum"),
    ("F41.9", "Gangguan cemas, tak spesifik"),
    ("F51.0", "Insomnia nonorganik"),
    ("F51.1", "Somnolensia nonorganik"),
    ("G40.9", "Epilepsi, tak spesifik"),
    ("G43.9", "Migrain, tak spesifik"),
    ("G45.9", "Serangan iskemik transitorial, tak spesifik"),
    ("G50.9", "Gangguan saraf trigeminus, tak spesifik"),
    ("G54.9", "Gangguan saraf perifer, tak spesifik"),
    ("G62.9", "Neuropati perifer, tak spesifik"),
    ("H01.0", "Blefaritis"),
    ("H10.9", "Konjungtivitis, tak spesifik"),
    ("H25.9", "Katarak senilis"),
    ("H52.1", "Miopi, tak spesifik"),
    ("H52.2", "Astigmatisma"),
    ("H65.9", "Otitis media, tak spesifik"),
    ("H66.9", "Otitis media supurativa, tak spesifik"),
    ("H92.0", "Nyeri telinga (otalgia)"),
    ("H92.1", "Kotoran telinga (otorrhea)"),
    ("I10", "Hipertensi esensial (primer)"),
    ("I11.9", "Penyakit jantung hipertensik"),
    ("I21.9", "Infark miokard akut, tak spesifik"),
    ("I25.9", "Penyakit jantung iskemik kronis"),
    ("I48.9", "Fibrilasi atrium dan flutter, tak spesifik"),
    ("I50.9", "Gagal jantung, tak spesifik"),
    ("I63.9", "Infark serebral, tak spesifik"),
    ("I69.3", "Sindrom post-infark serebral"),
    ("I73.9", "Penyakit pembuluh darah perifer, tak spesifik"),
    ("I84.9", "Ambeien (wasir), tak spesifik"),
    ("I87.2", "Insufisiensi vena kronis"),
    ("I95.9", "Hipotensi, tak spesifik"),
    ("J02.9", "Faringitis akut, tak spesifik"),
    ("J03.9", "Tonsilitis akut, tak spesifik"),
    ("J06.9", "Infeksi saluran napas atas akut, tak spesifik"),
    ("J11.1", "Influenza dengan manifestasi saluran napas lain"),
    ("J18.9", "Pneumonia, organisme tak spesifik"),
    ("J20.9", "Bronkitis akut, tak spesifik"),
    ("J21.9", "Bronkiolitis akut, tak spesifik"),
    ("J30.9", "Rinitis alergi, tak spesifik"),
    ("J31.2", "Faringitis kronis"),
    ("J32.9", "Sinusitis kronis, tak spesifik"),
    ("J33.9", "Polip hidung"),
    ("J35.0", "Tonsilitis kronis"),
    ("J36", "Abses peritonsilar"),
    ("J40", "Bronkitis, tak spesifik"),
    ("J42", "Bronkitis kronis, tak spesifik"),
    ("J44.1", "PPOK dengan eksaserbasi"),
    ("J45.0", "Asma alergik (atopik)"),
    ("J45.9", "Asma, tak spesifik"),
    ("J90", "Efusi pleura"),
    ("J98.9", "Penyakit saluran napas, tak spesifik"),
    ("K04.9", "Penyakit pulpa dan periapikal, tak spesifik"),
    ("K08.8", "Kehilangan gigi dan cacat gigi lain"),
    ("K12.2", "Stomatitis (radang mulut)"),
    ("K21.0", "GERD dengan esofagitis"),
    ("K21.9", "GERD tanpa esofagitis"),
    ("K25.9", "Ulkus lambung, tak spesifik"),
    ("K27.9", "Ulkus duodenum, tak spesifik"),
    ("K29.7", "Gastritis, tak spesifik"),
    ("K35.8", "Apendisitis akut tanpa komplikasi"),
    ("K40.9", "Hernia inguinalis tanpa obstruksi atau gangren"),
    ("K42.9", "Hernia umbilikal, tak spesifik"),
    ("K52.9", "Gastroenteritis noninfeksius, tak spesifik"),
    ("K56.6", "Obstruksi usus lain"),
    ("K59.0", "Konstipasi (sembelit)"),
    ("K60.9", "Fisura ani, tak spesifik"),
    ("K64.9", "Ambeien (wasir)"),
    ("K73.9", "Hepatitis kronis, tak spesifik"),
    ("K75.9", "Penyakit hati, tak spesifik"),
    ("K76.0", "Hati berlemak (steatosis hati)"),
    ("K80.2", "Calculus kandung tanpa kolesistitis"),
    ("K81.0", "Kolesistitis akut"),
    ("K83.0", "Kolangitis"),
    ("K85.9", "Pankreatitis akut, tak spesifik"),
    ("K92.2", "Perdarahan saluran cerna, tak spesifik"),
    ("L01.9", "Impetigo, tak spesifik"),
    ("L03.1", "Selulitis bagian lain tungkai"),
    ("L08.9", "Infeksi kulit setempat, tak spesifik"),
    ("L20.9", "Dermatitis atopik, tak spesifik"),
    ("L29.9", "Pruritus (gatal), tak spesifik"),
    ("L30.9", "Dermatitis, tak spesifik"),
    ("L40.9", "Psoriasis, tak spesifik"),
    ("L50.9", "Urtikaria, tak spesifik"),
    ("L70.9", "Akne (jerawat), tak spesifik"),
    ("L80", "Vitiligo"),
    ("L82", "Keratosis seboroik"),
    ("L89.9", "Dekubitus (luka tekan), tak spesifik"),
    ("M06.9", "Artritis reumatoid, tak spesifik"),
    ("M15.9", "Poliosteoartritis, tak spesifik"),
    ("M16.9", "Koxartrosis, tak spesifik"),
    ("M17.9", "Gonartrosis, tak spesifik"),
    ("M25.5", "Nyeri sendi"),
    ("M45.9", "Spondilitis ankilosa, tak spesifik"),
    ("M50.9", "Gangguan disc serviks, tak spesifik"),
    ("M51.9", "Gangguan disc lumbal, tak spesifik"),
    ("M54.2", "Nyeri leher (servikalgia)"),
    ("M54.5", "Nyeri punggung bawah"),
    ("M62.81", "Kelemahan otot"),
    ("M75.0", "Adhesive capsulitis bahu"),
    ("M75.1", "Sindrom rotator cuff"),
    ("M79.6", "Nyeri tungkai"),
    ("N20.0", "Calculus ginjal"),
    ("N32.8", "Gangguan kandung kemih lain"),
    ("N39.0", "Infeksi saluran kemih, tempat tak spesifik"),
    ("N40", "Hiperplasia prostat jinak"),
    ("N70", "Salpingitis dan ooforitis"),
    ("N76.0", "Vaginitis akut"),
    ("N92.6", "Menstruasi berlebihan atau irreguler"),
    ("N94.6", "Dismenore, tak spesifik"),
    ("N95.1", "Status klimakterium wanita"),
    ("O80", "Persalinan normal spontan"),
    ("O82", "Persalinan caesar"),
    ("P07.3", "Bayi pratermin lain"),
    ("P21.1", "Stres respirasi newborn"),
    ("Q21.1", "Cacat septum ventrikel"),
    ("R00.0", "Takikardia, tak spesifik"),
    ("R03.0", "Tekanan darah tinggi tanpa diagnosis hipertensi"),
    ("R04.0", "Epistaxis (mimisan)"),
    ("R05.9", "Batuk, tak spesifik"),
    ("R06.02", "Sesak napas (dispnea)"),
    ("R06.89", "Abnormalitas pernapasan lain"),
    ("R07.9", "Nyeri dada, tak spesifik"),
    ("R09.3", "Sputum abnormal"),
    ("R10.9", "Nyeri abdomen, tak spesifik"),
    ("R11", "Mual dan muntah"),
    ("R13", "Disfagia (kesulitan menelan)"),
    ("R14", "Perut kembung (distensi abdomen)"),
    ("R15", "Inkontinensia feses"),
    ("R17", "Ikterus, tak spesifik"),
    ("R19.7", "Perubahan kebiasaan buang air besar"),
    ("R21", "Ruam, tak spesifik"),
    ("R22.4", "Pembengkakan kulit setempat"),
    ("R25.2", "Kejang dan kram"),
    ("R31", "Hematuria, tak spesifik"),
    ("R32", "Inkontinensia urin, tak spesifik"),
    ("R33", "Retensi urin"),
    ("R40.2", "Koma, tak spesifik"),
    ("R41.0", "Gangguan orientasi"),
    ("R42", "Pusing dan pusing tuam"),
    ("R45.1", "Gelisah (restlessness)"),
    ("R50.9", "Demam, tak spesifik"),
    ("R51", "Nyeri kepala (sakit kepala)"),
    ("R53.1", "Kelemahan"),
    ("R55", "Pingsan (sinkope)"),
    ("R56.9", "Kejang, tak spesifik"),
    ("R60.0", "Edema setempat"),
    ("R60.9", "Edema, tak spesifik"),
    ("R63.0", "Anoreksia"),
    ("R63.4", "Penurunan berat badan abnormal"),
    ("R73.9", "Hiperglikemia, tak spesifik"),
    ("R79.9", "Temuan abnormal darah lain"),
    ("R80.9", "Proteinuria, tak spesifik"),
    ("S06.9", "Cedera intrakranial, tak spesifik"),
    ("S52.9", "Fraktur forearm, tak spesifik"),
    ("S72.0", "Fraktur leher femur"),
    ("T14.9", "Cedera, tak spesifik"),
    ("T78.2", "Syok anafilaksis, tak spesifik"),
    ("T78.4", "Reaksi alergi lain"),
    ("X59.9", "Paparan faktor penyebab, tak spesifik"),
    ("Z00.0", "Pemeriksaan medis umum"),
    ("Z09", "Follow-up setelah pengobatan"),
    ("Z20.8", "Kontak dengan penyakit menular lain"),
    ("Z23", "Imunisasi"),
    ("Z33.1", "Status hamil"),
    ("Z34.9", "Pengawasan kehamilan normal"),
    ("Z46.9", "Pemasangan atau penyesuaian alat medis lain"),
    ("Z51.8", "Aftercare lain"),
    ("Z71.3", "Konseling nutrisi dan diet"),
    ("Z71.9", "Konseling, tak spesifik"),
    ("Z72.0", "Penggunaan tembakau"),
    ("Z73.0", "Sindrom burnout"),
]

# ------------------------------------------------------------------------------
# Master obat (harga ilustratif dalam Rupiah)
# ------------------------------------------------------------------------------
DRUGS = [
    ("Paracetamol 500 mg", "tablet", "500"),
    ("Paracetamol sirup 120 mg/5 mL", "botol 60 mL", "12000"),
    ("Ibuprofen 400 mg", "tablet", "800"),
    ("Mefenamat 500 mg", "tablet", "1200"),
    ("Diclofenac 50 mg", "tablet", "900"),
    ("Ketorolac 30 mg", "ampul", "15000"),
    ("Amoksisilin 500 mg", "kapsul", "1500"),
    ("Amoksisilin + Klavulanat 625 mg", "tablet", "7000"),
    ("Azitromisin 500 mg", "tablet", "5000"),
    ("Ciprofloksasin 500 mg", "tablet", "3500"),
    ("Metronidazol 500 mg", "tablet", "700"),
    ("Oseltamivir 75 mg", "kapsul", "8000"),
    ("Cetirizin 10 mg", "tablet", "1000"),
    ("Loratadin 10 mg", "tablet", "1200"),
    ("Amlodipin 5 mg", "tablet", "1500"),
    ("Kaptopril 25 mg", "tablet", "800"),
    ("Losartan 50 mg", "tablet", "3000"),
    ("Metformin 500 mg", "tablet", "1000"),
    ("Glibenklamid 5 mg", "tablet", "900"),
    ("Simvastatin 20 mg", "tablet", "2500"),
    ("Omeprazol 20 mg", "kapsul", "1800"),
    ("Lansoprazol 30 mg", "kapsul", "4500"),
    ("Domperidone 10 mg", "tablet", "1200"),
    ("Ondansetron 4 mg", "tablet", "3000"),
    ("Oralit (ORS)", "sachet", "2000"),
    ("Zinc 20 mg", "tablet", "500"),
    ("Ambroksol 30 mg", "tablet", "900"),
    ("Salbutamol 2 mg", "tablet", "500"),
    ("Prednison 5 mg", "tablet", "1000"),
    ("Deksametason 0,5 mg", "tablet", "700"),
    ("Natrium klorida 0,9% 500 mL", "botol", "6000"),
    ("Glukosa 5% 500 mL", "botol", "7000"),
    ("Insulin human 100 IU/mL", "vial", "85000"),
    ("Vitamin B1 + B6 + B12", "tablet", "1500"),
    ("Vitamin C 500 mg", "tablet", "800"),
    ("Ferol (FeSO4 + asam folat)", "tablet", "500"),
    ("Antasida DOEN", "suspensi 150 mL", "9000"),
    ("Loperamid 2 mg", "tablet", "1000"),
]

# ------------------------------------------------------------------------------
# Master tindakan (biaya ilustratif dalam Rupiah)
# ------------------------------------------------------------------------------
PROCEDURES = [
    ("Konsultasi dokter umum", "50000"),
    ("Rawat inap (per hari)", "350000"),
    ("Injeksi intramuskular", "25000"),
    ("Injeksi intravena", "35000"),
    ("Nebulisasi", "75000"),
    ("Pemasangan infus", "50000"),
    ("Pemasangan oksigen nasal kanul", "40000"),
    ("Pemeriksaan gula darah sewaktu", "15000"),
    ("Pemasangan kateter urin", "60000"),
    ("Perawatan luka sederhana", "50000"),
    ("Elektrokardiografi (EKG)", "100000"),
    ("Imunisasi (suntik)", "50000"),
]


def seed_users(db: Session) -> int:
    count = 0
    for row in USERS:
        email = row["email"].lower().strip()
        exists = db.scalar(select(User).where(User.email == email))
        if exists is None:
            db.add(
                User(
                    email=email,
                    password_hash=hash_password(DEMO_PASSWORD),
                    full_name=row["full_name"],
                    role=row["role"],
                )
            )
            count += 1
    db.commit()
    return count


def seed_patients(db: Session) -> int:
    count = 0
    for mrn, name, birth_date, gender, address, phone in PATIENTS:
        exists = db.scalar(select(Patient).where(Patient.medical_record_no == mrn))
        if exists is None:
            db.add(
                Patient(
                    medical_record_no=mrn,
                    full_name=name,
                    birth_date=birth_date,
                    gender=gender,
                    address=address,
                    phone_number=phone,
                )
            )
            count += 1
    db.commit()
    return count


def seed_icd10(db: Session) -> int:
    count = 0
    for code, name in ICD10:
        if db.get(Icd10Master, code) is None:
            db.add(Icd10Master(code=code, name=name))
            count += 1
    db.commit()
    return count


def seed_drugs(db: Session) -> int:
    count = 0
    for name, unit, price in DRUGS:
        exists = db.scalar(select(DrugMaster).where(DrugMaster.name == name))
        if exists is None:
            db.add(DrugMaster(name=name, unit=unit, price=Decimal(price)))
            count += 1
    db.commit()
    return count


def seed_procedures(db: Session) -> int:
    count = 0
    for name, price in PROCEDURES:
        exists = db.scalar(select(ProcedureMaster).where(ProcedureMaster.name == name))
        if exists is None:
            db.add(ProcedureMaster(name=name, price=Decimal(price)))
            count += 1
    db.commit()
    return count


def seed_pipeline_logs(db: Session) -> int:
    """Seed data awal log & evaluasi pipeline untuk demonstrasi sidang."""
    count = 0
    existing = db.scalar(select(func.count()).select_from(PipelineLog))
    if existing and existing > 0:
        return 0

    logs_data = [
        {
            "model_version": "whisper-medium-fine-tuned (final)",
            "wer_value": 0.065,
            "soap_f1": 0.938,
            "ner_f1": 0.902,
            "latency_ms": {"stt": 790, "soap": 40, "ner": 58, "assertion": 25},
            "notes": "Pengujian benchmark skenario Demam Berdarah Dengue (Akurasi Tinggi)",
        },
        {
            "model_version": "whisper-medium-fine-tuned (epoch 5)",
            "wer_value": 0.078,
            "soap_f1": 0.925,
            "ner_f1": 0.894,
            "latency_ms": {"stt": 820, "soap": 45, "ner": 65, "assertion": 30},
            "notes": "Pengujian benchmark skenario Gastritis Akut & ISPA",
        },
        {
            "model_version": "whisper-medium-fine-tuned (epoch 3)",
            "wer_value": 0.095,
            "soap_f1": 0.910,
            "ner_f1": 0.880,
            "latency_ms": {"stt": 815, "soap": 42, "ner": 60, "assertion": 28},
            "notes": "Evaluasi checkpoint training epoch 3",
        },
        {
            "model_version": "whisper-medium-pretrained (baseline)",
            "wer_value": 0.182,
            "soap_f1": 0.875,
            "ner_f1": 0.830,
            "latency_ms": {"stt": 850, "soap": 48, "ner": 62, "assertion": 32},
            "notes": "Baseline model tanpa fine-tuning korpus medis (sebagai pembanding)",
        },
    ]

    for item in logs_data:
        db.add(PipelineLog(**item))
        count += 1
    db.commit()
    return count


def run_seed(db: Session) -> dict[str, int]:
    """Jalankan semua seed. Mengembalikan jumlah baris baru per tabel."""
    return {
        "users": seed_users(db),
        "patients": seed_patients(db),
        "icd10": seed_icd10(db),
        "drugs": seed_drugs(db),
        "procedures": seed_procedures(db),
        "pipeline_logs": seed_pipeline_logs(db),
    }


def main() -> None:
    session_factory = get_session_factory()
    db = session_factory()
    try:
        added = run_seed(db)
        print("Seed selesai. Baris baru ditambahkan:")
        for table, n in added.items():
            print(f"  - {table}: {n}")
        print(f"\nAkun demo (password: {DEMO_PASSWORD}):")
        for row in USERS:
            print(f"  - {row['email']} ({row['role']})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
