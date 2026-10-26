"""Unit test untuk NLP Mock Engine dan aturan pemetaan formulir RME (Fase 4)."""

from __future__ import annotations

from app.nlp.base import EntityResult, SentenceResult
from app.nlp.mock import MockAssertionEngine, MockNerEngine, MockSoapClassifier
from app.services.mapping import map_nlp_to_form


def test_soap_classifier_rules():
    classifier = MockSoapClassifier()
    sentences = [
        "Pasien mengeluh pusing dan demam sejak kemarin.",
        "Pada pemeriksaan fisik mata tampak merah dan konjungtiva anemis.",
        "Kesan diagnosis demam berdarah dengue.",
        "Diberikan paracetamol dan dianjurkan banyak minum air putih.",
    ]
    labels = classifier.classify(sentences)
    assert labels[0] == "S"  # Subjective
    assert labels[1] == "O"  # Objective
    assert labels[2] == "A"  # Assessment
    assert labels[3] == "P"  # Plan


def test_ner_and_assertion_negation():
    ner = MockNerEngine()
    assertion = MockAssertionEngine()

    sentences = [
        "Pasien mengeluh pusing dan demam tinggi.",
        "Tidak ada sesak napas dan tidak muntah.",
        "Pemeriksaan mata merah.",
        "Kesan demam berdarah.",
        "Diberikan paracetamol.",
    ]

    entities = ner.extract(sentences)
    assert len(entities) >= 5

    texts = [e.text.lower() for e in entities]
    assert "pusing" in texts
    assert "demam" in texts
    assert "sesak napas" in texts
    assert "mata merah" in texts
    assert "demam berdarah" in texts
    assert "paracetamol" in texts

    statuses = assertion.classify(sentences, entities)
    ent_status_map = {
        ent.text.lower(): stat for ent, stat in zip(entities, statuses, strict=False)
    }

    assert ent_status_map["pusing"] == "PRESENT"
    assert ent_status_map["demam"] == "PRESENT"
    assert ent_status_map["sesak napas"] == "ABSENT"


def test_mapping_absent_entity_never_enters_diagnosis_or_medication():
    """ATURAN KRUSIAL: Entitas ABSENT dilarang masuk ke tabel diagnosa atau obat aktif!"""
    sentences = [
        SentenceResult(idx=0, text="Tidak ada demam berdarah.", soap="A"),
        SentenceResult(idx=1, text="Tidak diberikan paracetamol.", soap="P"),
    ]
    entities = [
        EntityResult(
            text="demam berdarah",
            label="DIAGNOSIS",
            start=10,
            end=24,
            sentence_idx=0,
            assertion="ABSENT",
        ),
        EntityResult(
            text="paracetamol",
            label="OBAT",
            start=16,
            end=27,
            sentence_idx=1,
            assertion="ABSENT",
        ),
    ]

    mapped = map_nlp_to_form(sentences, entities)

    assert len(mapped.diagnoses) == 0
    assert len(mapped.medications) == 0


def test_mapping_full_sidang_scenario():
    """Pengujian skenario sidang proposal secara lengkap."""
    sentences = [
        SentenceResult(
            idx=0,
            text="Pasien mengeluh pusing, badan menggigil, dan muntah sejak dua hari.",
            soap="S",
        ),
        SentenceResult(idx=1, text="Tidak ada sesak napas.", soap="S"),
        SentenceResult(idx=2, text="Pada pemeriksaan mata tampak merah.", soap="O"),
        SentenceResult(idx=3, text="Kesan demam berdarah.", soap="A"),
        SentenceResult(
            idx=4,
            text="Diberikan paracetamol, dan dianjurkan banyak minum air putih.",
            soap="P",
        ),
    ]

    entities = [
        EntityResult(
            text="pusing",
            label="GEJALA",
            start=16,
            end=22,
            sentence_idx=0,
            assertion="PRESENT",
        ),
        EntityResult(
            text="badan menggigil",
            label="GEJALA",
            start=24,
            end=39,
            sentence_idx=0,
            assertion="PRESENT",
        ),
        EntityResult(
            text="muntah",
            label="GEJALA",
            start=45,
            end=51,
            sentence_idx=0,
            assertion="PRESENT",
        ),
        EntityResult(
            text="sesak napas",
            label="GEJALA",
            start=10,
            end=21,
            sentence_idx=1,
            assertion="ABSENT",
        ),
        EntityResult(
            text="mata merah",
            label="TANDA",
            start=25,
            end=35,
            sentence_idx=2,
            assertion="PRESENT",
        ),
        EntityResult(
            text="demam berdarah",
            label="DIAGNOSIS",
            start=6,
            end=20,
            sentence_idx=3,
            assertion="PRESENT",
        ),
        EntityResult(
            text="paracetamol",
            label="OBAT",
            start=10,
            end=21,
            sentence_idx=4,
            assertion="PRESENT",
        ),
    ]

    mapped = map_nlp_to_form(sentences, entities)

    assert "pusing" in mapped.anamnesis.lower()
    assert "badan menggigil" in mapped.anamnesis.lower()
    assert "muntah" in mapped.anamnesis.lower()
    assert "tidak ada sesak napas" in mapped.anamnesis.lower()

    eye_exam = next((o for o in mapped.physical_exam if o.body_site == "Mata"), None)
    assert eye_exam is not None
    assert not eye_exam.is_normal
    assert "mata merah" in eye_exam.finding.lower()

    lung_exam = next((o for o in mapped.physical_exam if o.body_site == "Paru"), None)
    assert lung_exam is not None
    assert lung_exam.is_normal

    assert len(mapped.diagnoses) == 1
    assert mapped.diagnoses[0].icd_code == "A91"
    assert "demam berdarah" in mapped.diagnoses[0].name.lower()

    assert len(mapped.medications) == 1
    assert "paracetamol" in mapped.medications[0].name.lower()

    assert "minum" in mapped.education.lower()
