"""Implementasi mesin NLP tiruan (Mock Engine) berbasis aturan (rule-based).

Sesuai Bagian 6 dokumen rancangan:
- MockSoapClassifier: klasifikasi kalimat ke SOAP berdasarkan kata kunci.
- MockNerEngine: ekstraksi entitas klinis (Gejala, Tanda, Diagnosis, Obat, Tindakan, Penunjang)
  berdasarkan pencocokan kamus dan leksikon medis.
- MockAssertionEngine: deteksi negasi (ABSENT), kemungkinan (POSSIBLE), dan ada (PRESENT).
"""

from __future__ import annotations

import re

from app.nlp.base import Entity

# -----------------------------------------------------------------------------
# 1. Mock Soap Classifier
# -----------------------------------------------------------------------------

SOAP_KEYWORDS = {
    "A": [
        "kesan",
        "diagnosis",
        "diagnosa",
        "suspek",
        "curiga",
        "pro ",
        "dd/",
        "kemungkinan menderita",
        "terkena",
        "terdiagnosis",
    ],
    "P": [
        "diberikan",
        "resep",
        "terapi",
        "anjuran",
        "kontrol",
        "edukasi",
        "dianjurkan",
        "disarankan",
        "minum",
        "obat",
        "istirahat",
        "rawat",
        "injeksi",
        "infus",
        "nebulisasi",
        "bedrest",
        "dosis",
    ],
    "O": [
        "pemeriksaan",
        "tampak",
        "ditemukan",
        "konjungtiva",
        "mata ",
        "tensi",
        "tekanan darah",
        "suhu",
        "nadi",
        "respirasi",
        "abdomen",
        "thorax",
        "paru",
        "jantung",
        "ekstremitas",
        "leher",
        "kulit",
        "ronkhi",
        "wheezing",
        "murmur",
        "auskultasi",
        "palpasi",
        "ikterik",
        "anemis",
        "hiperemis",
    ],
    "S": [
        "mengeluh",
        "keluhan",
        "riwayat",
        "sejak",
        "merasa",
        "badan",
        "pusing",
        "demam",
        "mual",
        "muntah",
        "sakit",
        "nyeri",
        "batuk",
        "sesak",
        "gatal",
        "lemas",
        "pasien",
        "tidak ada",
    ],
}


class MockSoapClassifier:
    """Klasifikasi kalimat ke S, O, A, P menggunakan aturan kata kunci."""

    def classify(self, sentences: list[str]) -> list[str]:
        results: list[str] = []
        for text in sentences:
            clean = text.lower()
            # Cek urutan prioritas: A -> P -> O -> S
            matched = "S"  # default
            if any(kw in clean for kw in SOAP_KEYWORDS["A"]):
                matched = "A"
            elif any(kw in clean for kw in SOAP_KEYWORDS["P"]):
                matched = "P"
            elif any(kw in clean for kw in SOAP_KEYWORDS["O"]):
                matched = "O"
            elif any(kw in clean for kw in SOAP_KEYWORDS["S"]):
                matched = "S"
            results.append(matched)
        return results


# -----------------------------------------------------------------------------
# 2. Mock NER Engine (Named Entity Recognition Medis)
# -----------------------------------------------------------------------------

DICTIONARY_ENTITIES: dict[str, list[str]] = {
    "DIAGNOSIS": [
        "demam berdarah dengue",
        "demam berdarah",
        "gastritis akut",
        "gastroenteritis akut",
        "faringitis akut",
        "infeksi saluran pernapasan akut",
        "diabetes melitus",
        "hipertensi primer",
        "demam tifoid",
        "hepatitis a",
        "dermatitis",
        "hipertensi",
        "gastritis",
        "ispa",
        "faringitis",
        "dbd",
        "asma",
    ],
    "OBAT": [
        "paracetamol",
        "parasetamol",
        "amoksisilin",
        "antasida doen",
        "antasida",
        "omeprazol",
        "lansoprazol",
        "ibuprofen",
        "asam mefenamat",
        "cetirizin",
        "loratadin",
        "oralit",
        "ors",
        "ambroksol",
        "salbutamol",
        "ondansetron",
        "domperidone",
        "metformin",
        "amlodipin",
        "vitamin c",
        "vitamin b",
        "dexamethasone",
        "deksametason",
    ],
    "TANDA": [
        "konjungtiva anemis",
        "mata tampak merah",
        "mata merah",
        "mata anemis",
        "nyeri tekan epigastrium",
        "perut kembung",
        "faring hiperemis",
        "sklera ikterik",
        "ruam kemerahan",
        "ruam merah",
        "ronkhi basah",
        "wheezing",
        "bising usus meningkat",
        "turgor kulit menurun",
        "edema tungkai",
    ],
    "GEJALA": [
        "badan menggigil",
        "badan meriang",
        "nyeri ulu hati",
        "sakit kepala",
        "sesak napas",
        "batuk berdahak",
        "batuk kering",
        "buang air besar cair",
        "nafsu makan menurun",
        "nyeri sendi",
        "nyeri dada",
        "sulit menelan",
        "menggigil",
        "pusing",
        "demam",
        "muntah",
        "mual",
        "batuk",
        "sesak",
        "diare",
        "lemas",
        "perih",
        "pegal",
    ],
    "TINDAKAN": [
        "rawat inap",
        "injeksi intramuskular",
        "injeksi intravena",
        "pemasangan infus",
        "nebulisasi",
        "elektrokardiografi",
        "perawatan luka",
        "ekg",
        "infus",
        "injeksi",
    ],
    "PENUNJANG": [
        "pemeriksaan darah lengkap",
        "darah lengkap",
        "uji trombosit",
        "swab antigen",
        "rontgen thorax",
        "laboratorium",
        "trombosit",
        "hematokrit",
    ],
}


class MockNerEngine:
    """Ekstraksi entitas klinis menggunakan kamus leksikon medis."""

    def extract(self, sentences: list[str]) -> list[Entity]:
        entities: list[Entity] = []

        for sent_idx, sentence in enumerate(sentences):
            clean_sent = sentence.lower()
            occupied_spans: list[tuple[int, int]] = []

            for label, terms in DICTIONARY_ENTITIES.items():
                for term in terms:
                    pattern = rf"\b{re.escape(term)}\b"
                    for match in re.finditer(pattern, clean_sent):
                        start, end = match.span()

                        overlap = any(
                            max(start, o_start) < min(end, o_end)
                            for o_start, o_end in occupied_spans
                        )
                        if not overlap:
                            occupied_spans.append((start, end))
                            matched_text = sentence[start:end]
                            entities.append(
                                Entity(
                                    text=matched_text,
                                    label=label,
                                    start=start,
                                    end=end,
                                    sentence_idx=sent_idx,
                                )
                            )

        entities.sort(key=lambda e: (e.sentence_idx, e.start))
        return entities


# -----------------------------------------------------------------------------
# 3. Mock Assertion / Negation Engine
# -----------------------------------------------------------------------------

NEGATION_PATTERNS = [
    r"\btidak\s+ada\b",
    r"\btidak\s+ditemukan\b",
    r"\btidak\s+tampak\b",
    r"\bbelum\s+tampak\b",
    r"\btanpa\b",
    r"\bbukan\b",
    r"\bmenyangkal\b",
    r"\bdisangkal\b",
    r"\bdisangkal\s+adanya\b",
    r"\btak\s+ada\b",
    r"\btak\s+tampak\b",
    r"\btidak\s+mengeluh\b",
]

POSSIBILITY_PATTERNS = [
    r"\bkemungkinan\b",
    r"\bmungkin\b",
    r"\bsuspek\b",
    r"\bcuriga\b",
    r"\bdiduga\b",
    r"\bpro\b",
]


class MockAssertionEngine:
    """Deteksi status assertion entitas: PRESENT | ABSENT | POSSIBLE."""

    def classify(self, sentences: list[str], entities: list[Entity]) -> list[str]:
        results: list[str] = []

        for ent in entities:
            if ent.sentence_idx >= len(sentences):
                results.append("PRESENT")
                continue

            sent_text = sentences[ent.sentence_idx].lower()
            pre_start = max(0, ent.start - 45)
            prefix_window = sent_text[pre_start:ent.start]

            # 1. Cek Negasi (ABSENT)
            is_negated = any(re.search(pat, prefix_window) for pat in NEGATION_PATTERNS)

            if not is_negated:
                for pat in NEGATION_PATTERNS:
                    match = re.search(pat, sent_text)
                    if match and match.start() < ent.start:
                        between = sent_text[match.end():ent.start]
                        if not re.search(r"\b(tetapi|namun|tapi|melainkan)\b", between):
                            is_negated = True
                            break

            if is_negated:
                results.append("ABSENT")
                continue

            # 2. Cek Dugaan / Kemungkinan (POSSIBLE)
            is_possible = any(re.search(pat, prefix_window) for pat in POSSIBILITY_PATTERNS)
            if is_possible:
                results.append("POSSIBLE")
                continue

            # 3. Default: PRESENT
            results.append("PRESENT")

        return results
