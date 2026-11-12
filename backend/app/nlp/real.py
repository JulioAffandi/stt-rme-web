"""Implementasi model NLP nyata (Real Engine) berbasis Transformer/IndoBERT.

Modul ini memuat model IndoBERT yang telah di-fine-tune untuk:
1. Klasifikasi kalimat SOAP dari `backend/models_store/soap_indobert`
2. Named Entity Recognition (NER) medis dari `backend/models_store/ner_indobert`
3. Deteksi negasi & assertion status dari `backend/models_store/assertion_indobert`
"""

from __future__ import annotations

import logging
from pathlib import Path

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoModelForTokenClassification,
    AutoTokenizer,
)

from app.nlp.base import AssertionEngine, Entity, NerEngine, SoapClassifier
from app.nlp.mock import MockAssertionEngine, MockNerEngine, MockSoapClassifier

logger = logging.getLogger(__name__)

DEFAULT_SOAP_MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "models_store" / "soap_indobert"
DEFAULT_NER_MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "models_store" / "ner_indobert"
DEFAULT_ASSERTION_MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "models_store" / "assertion_indobert"


class RealSoapClassifier:
    """Pengklasifikasi kalimat SOAP menggunakan model IndoBERT fine-tuned."""

    def __init__(self, model_path: Path | str = DEFAULT_SOAP_MODEL_PATH) -> None:
        self.model_path = Path(model_path)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if not self.model_path.exists() or not (self.model_path / "model.safetensors").exists():
            logger.warning(
                "Model IndoBERT SOAP tidak ditemukan di %s. Menggunakan MockSoapClassifier sebagai fallback.",
                self.model_path,
            )
            self._fallback: SoapClassifier | None = MockSoapClassifier()
            self.model = None
            self.tokenizer = None
        else:
            logger.info("Memuat model IndoBERT SOAP dari %s di device %s...", self.model_path, self.device)
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
            self.model = AutoModelForSequenceClassification.from_pretrained(str(self.model_path))
            self.model.to(self.device)
            self.model.eval()
            self.id2label = self.model.config.id2label
            self._fallback = None
            logger.info("Model IndoBERT SOAP berhasil dimuat!")

    def classify(self, sentences: list[str]) -> list[str]:
        if not sentences:
            return []

        if self._fallback is not None or self.model is None or self.tokenizer is None:
            return (self._fallback or MockSoapClassifier()).classify(sentences)

        inputs = self.tokenizer(
            sentences,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            preds = torch.argmax(outputs.logits, dim=1).tolist()

        return [self.id2label[p] for p in preds]


class RealNerEngine:
    """Ekstraksi entitas klinis menggunakan model IndoBERT Token Classification fine-tuned."""

    def __init__(self, model_path: Path | str = DEFAULT_NER_MODEL_PATH) -> None:
        self.model_path = Path(model_path)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if not self.model_path.exists() or not (self.model_path / "model.safetensors").exists():
            logger.warning(
                "Model IndoBERT NER tidak ditemukan di %s. Menggunakan MockNerEngine sebagai fallback.",
                self.model_path,
            )
            self._fallback: NerEngine | None = MockNerEngine()
            self.model = None
            self.tokenizer = None
        else:
            logger.info("Memuat model IndoBERT NER dari %s di device %s...", self.model_path, self.device)
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
            self.model = AutoModelForTokenClassification.from_pretrained(str(self.model_path))
            self.model.to(self.device)
            self.model.eval()
            self.id2label = self.model.config.id2label
            self._fallback = None
            logger.info("Model IndoBERT NER berhasil dimuat!")

    def extract(self, sentences: list[str]) -> list[Entity]:
        if not sentences:
            return []

        if self._fallback is not None or self.model is None or self.tokenizer is None:
            return (self._fallback or MockNerEngine()).extract(sentences)

        all_entities: list[Entity] = []

        for sent_idx, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            inputs = self.tokenizer(
                sentence,
                return_offsets_mapping=True,
                truncation=True,
                max_length=128,
                return_tensors="pt",
            ).to(self.device)

            offsets = inputs["offset_mapping"][0].tolist()

            with torch.no_grad():
                outputs = self.model(inputs["input_ids"], attention_mask=inputs["attention_mask"])
                preds = torch.argmax(outputs.logits[0], dim=1).tolist()

            current_ent: Entity | None = None
            for pred_id, (start, end) in zip(preds, offsets):
                if start == end:
                    continue
                tag = self.id2label[pred_id]
                if tag.startswith("B-"):
                    if current_ent:
                        all_entities.append(current_ent)
                    lbl = tag.split("-")[1]
                    current_ent = Entity(
                        text=sentence[start:end],
                        label=lbl,
                        start=start,
                        end=end,
                        sentence_idx=sent_idx,
                    )
                elif tag.startswith("I-"):
                    lbl = tag.split("-")[1]
                    if current_ent and current_ent.label == lbl:
                        current_ent.end = end
                        current_ent.text = sentence[current_ent.start:end]
                    else:
                        if current_ent:
                            all_entities.append(current_ent)
                        current_ent = Entity(
                            text=sentence[start:end],
                            label=lbl,
                            start=start,
                            end=end,
                            sentence_idx=sent_idx,
                        )
                else:
                    if current_ent:
                        all_entities.append(current_ent)
                        current_ent = None

            if current_ent:
                all_entities.append(current_ent)

        all_entities.sort(key=lambda e: (e.sentence_idx, e.start))
        return all_entities


class RealAssertionEngine:
    """Deteksi negasi dan status assertion entitas menggunakan model IndoBERT fine-tuned."""

    def __init__(self, model_path: Path | str = DEFAULT_ASSERTION_MODEL_PATH) -> None:
        self.model_path = Path(model_path)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if not self.model_path.exists() or not (self.model_path / "model.safetensors").exists():
            logger.warning(
                "Model IndoBERT Assertion tidak ditemukan di %s. Menggunakan MockAssertionEngine sebagai fallback.",
                self.model_path,
            )
            self._fallback: AssertionEngine | None = MockAssertionEngine()
            self.model = None
            self.tokenizer = None
        else:
            logger.info("Memuat model IndoBERT Assertion dari %s di device %s...", self.model_path, self.device)
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
            self.model = AutoModelForSequenceClassification.from_pretrained(str(self.model_path))
            self.model.to(self.device)
            self.model.eval()
            self.id2label = self.model.config.id2label
            self._fallback = None
            logger.info("Model IndoBERT Assertion berhasil dimuat!")

    def classify(self, sentences: list[str], entities: list[Entity]) -> list[str]:
        if not entities or not sentences:
            return []

        if self._fallback is not None or self.model is None or self.tokenizer is None:
            return (self._fallback or MockAssertionEngine()).classify(sentences, entities)

        queries = [f"Entitas: {ent.text}" for ent in entities]
        contexts = [
            sentences[ent.sentence_idx] if 0 <= ent.sentence_idx < len(sentences) else ""
            for ent in entities
        ]

        inputs = self.tokenizer(
            queries,
            contexts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            preds = torch.argmax(outputs.logits, dim=1).tolist()

        return [self.id2label[p] for p in preds]
