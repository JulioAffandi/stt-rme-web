"""Kontrak interface NLP sesuai Bagian 6 Dokumen Rancangan Website Demo RME.

Interface ini bersifat protokol murni agar modul STT, SOAP Classifier, NER,
dan Assertion Classifier dapat diganti secara modular tanpa mengubah API/frontend.
"""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field


class Segment(BaseModel):
    """Segmen audio dari hasil transkripsi speech-to-text."""

    start: float | None = None
    end: float | None = None
    text: str


class SttEngine(Protocol):
    """Protokol mesin Speech-to-Text."""

    def transcribe(self, wav_path: str) -> list[Segment]:
        """Transkripsikan file WAV 16kHz mono ke daftar segmen teks."""
        ...


class SoapClassifier(Protocol):
    """Protokol klasifikasi kalimat ke label SOAP (S, O, A, P)."""

    def classify(self, sentences: list[str]) -> list[str]:
        ...


class Entity(BaseModel):
    """Entitas klinis yang diekstraksi dari kalimat."""

    text: str
    label: str  # GEJALA | TANDA | DIAGNOSIS | OBAT | TINDAKAN | PENUNJANG
    start: int  # offset karakter awal pada kalimat
    end: int  # offset karakter akhir pada kalimat
    sentence_idx: int


class NerEngine(Protocol):
    """Protokol Named Entity Recognition medis."""

    def extract(self, sentences: list[str]) -> list[Entity]:
        ...


class AssertionEngine(Protocol):
    """Protokol deteksi negasi dan status assertion entitas."""

    def classify(self, sentences: list[str], entities: list[Entity]) -> list[str]:
        """Mengembalikan list status: 'PRESENT' | 'ABSENT' | 'POSSIBLE' sejajar dengan entities."""
        ...


class SentenceResult(BaseModel):
    idx: int
    text: str
    soap: str = "S"  # S | O | A | P


class EntityResult(BaseModel):
    text: str
    label: str  # GEJALA | TANDA | DIAGNOSIS | OBAT | TINDAKAN | PENUNJANG
    start: int
    end: int
    sentence_idx: int
    assertion: str = "PRESENT"  # PRESENT | ABSENT | POSSIBLE


class TimingsResult(BaseModel):
    stt: int = 0
    soap: int = 0
    ner: int = 0
    assertion: int = 0


class PipelineResult(BaseModel):
    """Format hasil pipeline (kontrak API resmi ke frontend)."""

    transcript: str
    sentences: list[SentenceResult] = Field(default_factory=list)
    entities: list[EntityResult] = Field(default_factory=list)
    timings_ms: TimingsResult = Field(default_factory=TimingsResult)
    segments: list[Segment] = Field(default_factory=list)
    mapped_form: dict[str, Any] | None = None
