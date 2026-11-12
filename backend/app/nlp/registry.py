"""Registry pemilihan modul NLP (STT, SOAP, NER, Assertion).

Memilih implementasi nyata atau mock berdasarkan konfigurasi `NLP_ENGINE`.
"""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.nlp.base import AssertionEngine, NerEngine, SoapClassifier, SttEngine
from app.nlp.mock import MockAssertionEngine, MockNerEngine, MockSoapClassifier
from app.nlp.stt_whisper import get_whisper_engine

logger = logging.getLogger(__name__)

_SOAP_CLASSIFIER: SoapClassifier | None = None
_NER_ENGINE: NerEngine | None = None
_ASSERTION_ENGINE: AssertionEngine | None = None


def get_stt_engine() -> SttEngine:
    """Mengembalikan engine STT Whisper."""
    return get_whisper_engine()


def get_soap_classifier() -> SoapClassifier:
    """Mengembalikan implementasi classifier SOAP."""
    global _SOAP_CLASSIFIER
    if _SOAP_CLASSIFIER is None:
        settings = get_settings()
        if settings.nlp_engine == "mock":
            _SOAP_CLASSIFIER = MockSoapClassifier()
        else:
            # Fase 5: Integrasi model IndoBERT nyata
            try:
                from app.nlp.real import RealSoapClassifier

                logger.info("Menggunakan RealSoapClassifier (IndoBERT fine-tuned)")
                _SOAP_CLASSIFIER = RealSoapClassifier()
            except Exception as e:
                logger.error("Gagal memuat RealSoapClassifier: %s. Fallback ke mock.", e)
                _SOAP_CLASSIFIER = MockSoapClassifier()
    return _SOAP_CLASSIFIER


def get_ner_engine() -> NerEngine:
    """Mengembalikan implementasi NER medis."""
    global _NER_ENGINE
    if _NER_ENGINE is None:
        settings = get_settings()
        if settings.nlp_engine == "mock":
            _NER_ENGINE = MockNerEngine()
        else:
            # Fase 5: Integrasi model NER Transformer nyata
            try:
                from app.nlp.real import RealNerEngine

                logger.info("Menggunakan RealNerEngine (IndoBERT fine-tuned)")
                _NER_ENGINE = RealNerEngine()
            except Exception as e:
                logger.error("Gagal memuat RealNerEngine: %s. Fallback ke mock.", e)
                _NER_ENGINE = MockNerEngine()
    return _NER_ENGINE


def get_assertion_engine() -> AssertionEngine:
    """Mengembalikan implementasi deteksi negasi dan assertion."""
    global _ASSERTION_ENGINE
    if _ASSERTION_ENGINE is None:
        settings = get_settings()
        if settings.nlp_engine == "mock":
            _ASSERTION_ENGINE = MockAssertionEngine()
        else:
            # Integrasi assertion Transformer IndoBERT fine-tuned
            try:
                from app.nlp.real import RealAssertionEngine

                logger.info("Menggunakan RealAssertionEngine (IndoBERT fine-tuned)")
                _ASSERTION_ENGINE = RealAssertionEngine()
            except Exception as e:
                logger.error("Gagal memuat RealAssertionEngine: %s. Fallback ke mock.", e)
                _ASSERTION_ENGINE = MockAssertionEngine()
    return _ASSERTION_ENGINE
