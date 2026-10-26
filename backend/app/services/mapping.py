"""Layanan pemetaan murni (Pure Function) dari hasil NLP ke Formulir & Database RME.

Sesuai Bagian 7 Dokumen Rancangan:
- Fungsi murni tanpa I/O DB untuk memudahkan unit testing.
- Pemetaan SOAP + Entitas + Assertion ke field: Anamnesa, 12 Organ Fisik,
  Diagnosa (ICD-10), Obat (Drug), Tindakan (Procedure), dan Edukasi.
- Aturan ketat: Entitas dengan assertion ABSENT DILARANG masuk ke tabel diagnosis/obat aktif!
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from app.nlp.base import EntityResult, SentenceResult

# 12 Organ Pemeriksaan Fisik Standar
PHYSICAL_EXAM_ORGANS = [
    "Kepala",
    "Mata",
    "Telinga",
    "Leher",
    "Thorax",
    "Paru",
    "Jantung",
    "Abdomen",
    "Inguinal",
    "Ekstremitas Atas",
    "Ekstremitas Bawah",
    "Kulit",
]

# Kamus Sinonim Organ Tubuh
ORGAN_SYNONYMS: dict[str, list[str]] = {
    "Mata": ["mata", "konjungtiva", "sklera", "pupil", "palpebra", "penglihatan", "visus"],
    "Paru": ["paru", "pulmo", "napas", "ronkhi", "wheezing", "suara napas", "vesikuler"],
    "Jantung": ["jantung", "cor", "murmur", "gallop", "bunyi jantung", "bj i", "bj ii"],
    "Abdomen": [
        "perut",
        "abdomen",
        "epigastrium",
        "lambung",
        "hepar",
        "hati",
        "lien",
        "limpa",
        "bising usus",
        "kembung",
    ],
    "Telinga": ["telinga", "auris", "pendengaran", "liang telinga", "membran timpani"],
    "Leher": [
        "leher",
        "colli",
        "tiroid",
        "jvp",
        "jugularis",
        "kelenjar getah bening",
        "faring",
        "tenggorokan",
    ],
    "Kepala": ["kepala", "caput", "rambut", "wajah", "bibir", "lidah"],
    "Thorax": ["thorax", "toraks", "dada", "dinding dada", "retraksi"],
    "Kulit": [
        "kulit",
        "turgor",
        "ruam",
        "eritema",
        "petekie",
        "ptekie",
        "purpura",
        "gatal",
        "integumen",
    ],
    "Ekstremitas Atas": ["ekstremitas atas", "tangan", "lengan", "telapak tangan", "jari tangan"],
    "Ekstremitas Bawah": [
        "ekstremitas bawah",
        "kaki",
        "tungkai",
        "lutut",
        "betis",
        "edema tungkai",
        "jari kaki",
    ],
    "Inguinal": ["inguinal", "selangkangan", "genital", "genitalia"],
}

# Kamus pencocokan diagnosis ke ICD-10
COMMON_ICD_MAP: dict[str, tuple[str, str]] = {
    "demam berdarah": ("A91", "Demam berdarah dengue"),
    "demam berdarah dengue": ("A91", "Demam berdarah dengue"),
    "dbd": ("A91", "Demam berdarah dengue"),
    "gastritis": ("K29.7", "Gastritis, tak spesifik"),
    "gastritis akut": ("K29.0", "Gastritis hemoragik akut"),
    "gastroenteritis": ("A09", "Diare dan gastroenteritis infeksius"),
    "ispa": ("J06.9", "Infeksi saluran pernapasan akut, tak spesifik"),
    "faringitis": ("J02.9", "Faringitis akut, tak spesifik"),
    "faringitis akut": ("J02.9", "Faringitis akut, tak spesifik"),
    "demam tifoid": ("A01.0", "Demam tifoid"),
    "tifoid": ("A01.0", "Demam tifoid"),
    "hipertensi": ("I10", "Hipertensi esensial (primer)"),
    "diabetes melitus": ("E11.9", "Diabetes melitus tipe 2 tanpa komplikasi"),
    "asma": ("J45.9", "Asma, tak spesifik"),
}

# Kamus pencocokan obat umum ke master obat
COMMON_DRUG_MAP: dict[str, tuple[int, str, int]] = {
    "paracetamol": (1, "Paracetamol 500 mg", 10),
    "parasetamol": (1, "Paracetamol 500 mg", 10),
    "amoksisilin": (5, "Amoksisilin 500 mg", 15),
    "antasida": (35, "Antasida DOEN", 1),
    "antasida doen": (35, "Antasida DOEN", 1),
    "omeprazol": (19, "Omeprazol 20 mg", 10),
    "ibuprofen": (2, "Ibuprofen 400 mg", 10),
    "cetirizin": (11, "Cetirizin 10 mg", 10),
    "oralit": (23, "Oralit (ORS)", 5),
    "ors": (23, "Oralit (ORS)", 5),
    "salbutamol": (26, "Salbutamol 2 mg", 10),
    "domperidone": (21, "Domperidone 10 mg", 10),
    "ondansetron": (22, "Ondansetron 4 mg", 6),
    "vitamin c": (33, "Vitamin C 500 mg", 10),
}


class MappedPhysicalExam(BaseModel):
    body_site: str
    finding: str
    is_normal: bool = True
    source: str = "ai"


class MappedDiagnosis(BaseModel):
    icd_code: str | None = None
    name: str
    assertion: str = "PRESENT"
    source: str = "ai"


class MappedMedication(BaseModel):
    drug_id: int | None = None
    name: str
    quantity: int = 1
    source: str = "ai"


class MappedProcedure(BaseModel):
    procedure_id: int | None = None
    name: str
    source: str = "ai"


class MappedFormResult(BaseModel):
    """Hasil pemetaan AI yang siap diterapkan ke Formulir Pemeriksaan RME."""

    anamnesis: str = ""
    physical_exam: list[MappedPhysicalExam] = Field(default_factory=list)
    diagnoses: list[MappedDiagnosis] = Field(default_factory=list)
    medications: list[MappedMedication] = Field(default_factory=list)
    procedures: list[MappedProcedure] = Field(default_factory=list)
    education: str = ""
    summary_text: str = ""


def find_matching_organ(finding_text: str) -> str | None:
    """Mencari organ tubuh yang cocok dari teks temuan fisik berdasarkan kamus sinonim."""
    clean = finding_text.lower()
    for organ, synonyms in ORGAN_SYNONYMS.items():
        if any(re.search(rf"\b{re.escape(syn)}\b", clean) for syn in synonyms):
            return organ
    return None


def map_nlp_to_form(
    sentences: list[SentenceResult],
    entities: list[EntityResult],
) -> MappedFormResult:
    """Fungsi murni: Mengonversi kalimat berlabel SOAP dan entitas ke formulir RME."""
    active_complaints: list[str] = []
    denied_complaints: list[str] = []
    possible_complaints: list[str] = []

    organ_map: dict[str, str] = {org: "Normal" for org in PHYSICAL_EXAM_ORGANS}
    organ_checked: dict[str, bool] = {org: False for org in PHYSICAL_EXAM_ORGANS}

    mapped_diagnoses: list[MappedDiagnosis] = []
    mapped_medications: list[MappedMedication] = []
    mapped_procedures: list[MappedProcedure] = []
    education_lines: list[str] = []

    for ent in entities:
        ent_text_clean = ent.text.strip().lower()

        if ent.label == "GEJALA":
            if ent.assertion == "PRESENT":
                if ent.text not in active_complaints:
                    active_complaints.append(ent.text)
            elif ent.assertion == "ABSENT":
                neg_text = f"Tidak ada {ent.text}"
                if neg_text not in denied_complaints:
                    denied_complaints.append(neg_text)
            elif ent.assertion == "POSSIBLE":
                poss_text = f"Kemungkinan {ent.text}"
                if poss_text not in possible_complaints:
                    possible_complaints.append(poss_text)

        elif ent.label == "TANDA":
            if ent.assertion == "PRESENT":
                matched_organ = find_matching_organ(ent.text)
                if matched_organ:
                    prev = organ_map[matched_organ]
                    new_val = ent.text if prev == "Normal" else f"{prev}, {ent.text}"
                    organ_map[matched_organ] = new_val
                    organ_checked[matched_organ] = True

        elif ent.label == "DIAGNOSIS":
            # ATURAN KRUSIAL: Entitas ABSENT DILARANG masuk tabel Diagnosa!
            if ent.assertion == "PRESENT":
                icd_match = COMMON_ICD_MAP.get(ent_text_clean)
                code = icd_match[0] if icd_match else None
                name = icd_match[1] if icd_match else ent.text.title()

                if not any(d.name.lower() == name.lower() for d in mapped_diagnoses):
                    mapped_diagnoses.append(
                        MappedDiagnosis(icd_code=code, name=name, assertion="PRESENT", source="ai")
                    )

        elif ent.label == "OBAT":
            if ent.assertion == "PRESENT":
                drug_match = COMMON_DRUG_MAP.get(ent_text_clean)
                drug_id = drug_match[0] if drug_match else None
                drug_name = drug_match[1] if drug_match else ent.text.title()
                qty = drug_match[2] if drug_match else 10

                if not any(m.name.lower() == drug_name.lower() for m in mapped_medications):
                    mapped_medications.append(
                        MappedMedication(
                            drug_id=drug_id, name=drug_name, quantity=qty, source="ai"
                        )
                    )

        elif ent.label == "TINDAKAN":
            if ent.assertion == "PRESENT":
                proc_name = ent.text.title()
                if not any(p.name.lower() == proc_name.lower() for p in mapped_procedures):
                    mapped_procedures.append(
                        MappedProcedure(procedure_id=None, name=proc_name, source="ai")
                    )

    for sent in sentences:
        sent_clean = sent.text.lower()
        if sent.soap == "P":
            if any(
                kw in sent_clean
                for kw in [
                    "anjuran",
                    "dianjurkan",
                    "edukasi",
                    "banyak minum",
                    "istirahat",
                    "hindari",
                    "kontrol",
                ]
            ):
                education_lines.append(sent.text.strip())

    anamnesis_parts: list[str] = []
    if active_complaints:
        anamnesis_parts.append(f"Keluhan: {', '.join(active_complaints)}.")
    if denied_complaints:
        anamnesis_parts.append(f"{'. '.join(denied_complaints)}.")
    if possible_complaints:
        anamnesis_parts.append(f"{'. '.join(possible_complaints)}.")

    if not anamnesis_parts:
        s_sentences = [s.text.strip() for s in sentences if s.soap == "S"]
        if s_sentences:
            anamnesis_parts.append(" ".join(s_sentences))

    final_anamnesis = " ".join(anamnesis_parts).strip()
    final_education = " ".join(education_lines).strip()

    final_physical: list[MappedPhysicalExam] = []
    for organ in PHYSICAL_EXAM_ORGANS:
        is_norm = not organ_checked[organ]
        final_physical.append(
            MappedPhysicalExam(
                body_site=organ,
                finding=organ_map[organ],
                is_normal=is_norm,
                source="ai" if not is_norm else "manual",
            )
        )

    summary_items: list[str] = []
    if final_anamnesis:
        summary_items.append("Anamnesa")
    active_organs = [o.body_site for o in final_physical if not o.is_normal]
    if active_organs:
        summary_items.append(f"Fisik ({', '.join(active_organs)})")
    if mapped_diagnoses:
        summary_items.append(f"Diagnosa ({len(mapped_diagnoses)})")
    if mapped_medications:
        summary_items.append(f"Obat ({len(mapped_medications)})")
    if mapped_procedures:
        summary_items.append(f"Tindakan ({len(mapped_procedures)})")
    if final_education:
        summary_items.append("Edukasi")

    summary_text = (
        f"Akan mengisi form: {', '.join(summary_items)}"
        if summary_items
        else "Belum ada entitas yang terpetakan ke form"
    )

    return MappedFormResult(
        anamnesis=final_anamnesis,
        physical_exam=final_physical,
        diagnoses=mapped_diagnoses,
        medications=mapped_medications,
        procedures=mapped_procedures,
        education=final_education,
        summary_text=summary_text,
    )
