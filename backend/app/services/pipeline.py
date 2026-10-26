"""Layanan orkestrasi pipeline dikte medis, STT, dan NLP.

Mengelola:
- Antrean eksekusi (Semaphore) agar hanya 1 proses Whisper/NLP berjalan pada satu waktu.
- Eksekusi background task bertahap:
  1. STT: Whisper transcribe audio ke WAV 16kHz
  2. SOAP: Klasifikasi kalimat ke S, O, A, P
  3. NER: Ekstraksi entitas medis (Gejala, Tanda, Diagnosis, Obat, Tindakan)
  4. Assertion: Deteksi status negasi (ABSENT), kemungkinan (POSSIBLE), dan ada (PRESENT)
  5. Mapping: Pemetaan murni ke formulir RME
- Pembaruan status berkala pada tabel `dictation_job` dan pencatatan ke `pipeline_log`.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time

from app.db.session import SessionLocal
from app.models.pipeline import DictationJob, PipelineLog
from app.nlp.base import EntityResult, PipelineResult, SentenceResult, TimingsResult
from app.nlp.registry import (
    get_assertion_engine,
    get_ner_engine,
    get_soap_classifier,
    get_stt_engine,
)
from app.services.mapping import map_nlp_to_form

logger = logging.getLogger(__name__)

# Semaphore global: hanya 1 inferensi STT/NLP berjalan sekaligus untuk mencegah OOM pada GPU/RAM
_PIPELINE_SEMAPHORE = asyncio.Semaphore(1)


def split_into_sentences(text: str) -> list[str]:
    """Memecah teks transkrip menjadi kalimat-kalimat terpisah."""
    if not text:
        return []
    # Pisahkan berdasarkan tanda titik, seru, tanya, atau baris baru
    raw_sentences = re.split(r"(?<=[.!?\n])\s+", text)
    sentences = [s.strip() for s in raw_sentences if s.strip()]
    return sentences if sentences else [text.strip()]


async def execute_dictation_job(
    job_id: int,
    encounter_id: int,
    audio_id: int,
    wav_path: str,
) -> None:
    """Task asinkron yang memproses seluruh pipeline STT + NLP di background."""
    async with _PIPELINE_SEMAPHORE:
        logger.info(
            "Memulai pemrosesan dictation job #%s (encounter #%s, audio #%s)",
            job_id,
            encounter_id,
            audio_id,
        )

        db = SessionLocal()
        try:
            job = db.get(DictationJob, job_id)
            if not job:
                logger.error("Dictation job #%s tidak ditemukan di DB", job_id)
                return

            # Update ke status processing: stt
            job.status = "processing"
            job.step = "stt"
            db.commit()

            # -----------------------------------------------------------------
            # Tahap 1: Whisper STT
            # -----------------------------------------------------------------
            t_stt_start = time.perf_counter()
            stt_engine = get_stt_engine()

            loop = asyncio.get_running_loop()
            segments = await loop.run_in_executor(None, stt_engine.transcribe, wav_path)
            stt_latency_ms = int((time.perf_counter() - t_stt_start) * 1000)

            full_transcript = " ".join(seg.text for seg in segments if seg.text).strip()

            # Pecah kalimat
            sentence_texts = split_into_sentences(full_transcript)
            if not sentence_texts and full_transcript:
                sentence_texts = [full_transcript]

            # -----------------------------------------------------------------
            # Tahap 2: SOAP Classification
            # -----------------------------------------------------------------
            job.step = "soap"
            db.commit()

            t_soap_start = time.perf_counter()
            soap_classifier = get_soap_classifier()
            soap_labels = await loop.run_in_executor(None, soap_classifier.classify, sentence_texts)
            soap_latency_ms = int((time.perf_counter() - t_soap_start) * 1000)

            sentences: list[SentenceResult] = []
            for idx, text in enumerate(sentence_texts):
                soap_label = soap_labels[idx] if idx < len(soap_labels) else "S"
                sentences.append(SentenceResult(idx=idx, text=text, soap=soap_label))

            # -----------------------------------------------------------------
            # Tahap 3: NER (Named Entity Recognition) Medis
            # -----------------------------------------------------------------
            job.step = "ner"
            db.commit()

            t_ner_start = time.perf_counter()
            ner_engine = get_ner_engine()
            raw_entities = await loop.run_in_executor(None, ner_engine.extract, sentence_texts)
            ner_latency_ms = int((time.perf_counter() - t_ner_start) * 1000)

            # -----------------------------------------------------------------
            # Tahap 4: Assertion / Deteksi Negasi
            # -----------------------------------------------------------------
            job.step = "assertion"
            db.commit()

            t_assert_start = time.perf_counter()
            assertion_engine = get_assertion_engine()
            assertion_statuses = await loop.run_in_executor(
                None, assertion_engine.classify, sentence_texts, raw_entities
            )
            assertion_latency_ms = int((time.perf_counter() - t_assert_start) * 1000)

            # Gabungkan entitas dengan status assertion
            entities: list[EntityResult] = []
            for idx, ent in enumerate(raw_entities):
                status_val = (
                    assertion_statuses[idx] if idx < len(assertion_statuses) else "PRESENT"
                )
                entities.append(
                    EntityResult(
                        text=ent.text,
                        label=ent.label,
                        start=ent.start,
                        end=ent.end,
                        sentence_idx=ent.sentence_idx,
                        assertion=status_val,
                    )
                )

            # -----------------------------------------------------------------
            # Tahap 5: Pemetaan ke Form RME
            # -----------------------------------------------------------------
            job.step = "mapping"
            db.commit()

            mapped_form = map_nlp_to_form(sentences, entities)

            # -----------------------------------------------------------------
            # Tahap 6: Finalisasi Hasil & Catat Pipeline Log
            # -----------------------------------------------------------------
            timings = TimingsResult(
                stt=stt_latency_ms,
                soap=soap_latency_ms,
                ner=ner_latency_ms,
                assertion=assertion_latency_ms,
            )

            result = PipelineResult(
                transcript=full_transcript,
                sentences=sentences,
                entities=entities,
                timings_ms=timings,
                segments=segments,
                mapped_form=mapped_form.model_dump(),
            )

            job.status = "done"
            job.step = "done"
            job.result_json = result.model_dump()
            job.error = None

            # Catat ke tabel pipeline_log untuk halaman evaluasi sidang
            log_entry = PipelineLog(
                encounter_id=encounter_id,
                model_version="whisper-medium+nlp-mock-v1",
                latency_ms=timings.model_dump(),
                notes=f"Transkrip: {len(full_transcript)} chars, {len(entities)} entities",
            )
            db.add(log_entry)
            db.commit()

            logger.info(
                "Pipeline dikte #%s sukses. Latensi: STT=%dms, SOAP=%dms, NER=%dms. Entitas=%d",
                job_id,
                stt_latency_ms,
                soap_latency_ms,
                ner_latency_ms,
                len(entities),
            )

        except Exception as exc:
            logger.exception("Gagal memproses pipeline dictation job #%s: %s", job_id, exc)
            try:
                job = db.get(DictationJob, job_id)
                if job:
                    job.status = "error"
                    job.error = str(exc)
                    db.commit()
            except Exception as db_exc:
                logger.error("Gagal memperbarui status error job #%s: %s", job_id, db_exc)
        finally:
            db.close()
