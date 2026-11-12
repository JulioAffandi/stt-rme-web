"""Skrip pelatihan (fine-tuning) model IndoBERT untuk Deteksi Negasi & Assertion klinis.

Menggunakan arsitektur Cross-Attention Sequence Pair:
- Text A: `Entitas: <nama entitas>`
- Text B: `<kalimat konteks>`
- Target: 3 kelas (PRESENT, ABSENT, POSSIBLE)

Input: `data/nlp_datasets/ner_assertion.json` (6.037 entitas teranotasi)
Output:
- Model checkpoint tersimpan di `backend/models_store/assertion_indobert/`
- Laporan evaluasi lengkap tersimpan di `backend/models_store/assertion_indobert/eval_report.json`
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATASET = PROJECT_ROOT / "data" / "nlp_datasets" / "ner_assertion.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "backend" / "models_store" / "assertion_indobert"
DEFAULT_MODEL_NAME = "indobenchmark/indobert-base-p1"

LABEL2ID = {"PRESENT": 0, "ABSENT": 1, "POSSIBLE": 2}
ID2LABEL = {0: "PRESENT", 1: "ABSENT", 2: "POSSIBLE"}


def compute_metrics(eval_pred):
    from sklearn.metrics import accuracy_score, classification_report, precision_recall_fscore_support

    predictions, labels = eval_pred
    preds = np.argmax(predictions, axis=1)

    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="macro", zero_division=0)
    acc = accuracy_score(labels, preds)

    report = classification_report(
        labels,
        preds,
        target_names=["PRESENT", "ABSENT", "POSSIBLE"],
        output_dict=True,
        zero_division=0,
    )

    metrics = {
        "accuracy": acc,
        "f1_macro": f1,
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_PRESENT": report["PRESENT"]["f1-score"],
        "f1_ABSENT": report["ABSENT"]["f1-score"],
        "f1_POSSIBLE": report["POSSIBLE"]["f1-score"],
    }
    return metrics


def main() -> None:
    from sklearn.model_selection import train_test_split
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    parser = argparse.ArgumentParser(description="Fine-tune IndoBERT untuk Assertion/Negation")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET, help="Path ke file dataset JSON")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_NAME, help="Pretrained model HF")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR, help="Folder output model")
    parser.add_argument("--epochs", type=int, default=3, help="Jumlah epoch pelatihan (default: 3)")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size (default: 32)")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate (default: 3e-5)")
    parser.add_argument("--max-len", type=int, default=128, help="Max sequence length (default: 128)")
    args = parser.parse_args()

    print("=" * 60)
    print("PELATIHAN MODEL INDOBERT UNTUK DETEKSI NEGASI / ASSERTION")
    print("=" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device komputasi: {device.upper()}")
    if device == "cuda":
        print(f"Nama GPU: {torch.cuda.get_device_name(0)}")
        print(f"Total VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

    if not args.data.exists():
        print(f"ERROR: Dataset tidak ditemukan di {args.data}")
        sys.exit(1)

    print(f"\nMemuat dataset dari {args.data}...")
    raw_data = json.loads(args.data.read_text(encoding="utf-8"))

    # Ekstrak pasangan (entitas, kalimat) -> assertion
    records = []
    for row in raw_data:
        sent = row["sentence"]
        for ent in row.get("entities", []):
            ass = ent.get("assertion", "PRESENT").upper()
            if ass in LABEL2ID:
                records.append({
                    "entity_text": f"Entitas: {ent['text']}",
                    "sentence": sent,
                    "assertion": ass,
                    "label": LABEL2ID[ass],
                })

    df = pd.DataFrame(records)
    print(f"Total pasangan entitas-konteks: {len(df)}")
    print("Distribusi kelas Assertion:")
    for ass_name, ass_id in LABEL2ID.items():
        count = (df["label"] == ass_id).sum()
        pct = (count / len(df)) * 100
        print(f"  [{ass_name}] {ass_id}: {count} ({pct:.1f}%)")

    # Stratified Train/Val/Test Split (80% / 10% / 10%)
    train_df, temp_df = train_test_split(df, test_size=0.20, random_state=42, stratify=df["label"])
    val_df, test_df = train_test_split(temp_df, test_size=0.50, random_state=42, stratify=temp_df["label"])

    print(f"\nPembagian data:")
    print(f"  Train : {len(train_df)} entitas")
    print(f"  Val   : {len(val_df)} entitas")
    print(f"  Test  : {len(test_df)} entitas")

    print(f"\nMemuat tokenizer: {args.model}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model)

    class ClinicalAssertionDataset(torch.utils.data.Dataset):
        def __init__(self, entities, sentences, labels):
            self.encodings = tokenizer(
                entities,
                sentences,
                truncation=True,
                padding=True,
                max_length=args.max_len,
                return_tensors="pt",
            )
            self.labels = labels

        def __len__(self):
            return len(self.labels)

        def __getitem__(self, idx):
            item = {key: val[idx] for key, val in self.encodings.items()}
            item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
            return item

    train_dataset = ClinicalAssertionDataset(
        train_df["entity_text"].tolist(), train_df["sentence"].tolist(), train_df["label"].tolist()
    )
    val_dataset = ClinicalAssertionDataset(
        val_df["entity_text"].tolist(), val_df["sentence"].tolist(), val_df["label"].tolist()
    )
    test_dataset = ClinicalAssertionDataset(
        test_df["entity_text"].tolist(), test_df["sentence"].tolist(), test_df["label"].tolist()
    )

    print(f"Memuat model klasifikasi: {args.model} (3 labels)...")
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model,
        num_labels=3,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True,
    )

    args.output.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(args.output / "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        fp16=(device == "cuda"),
        logging_steps=20,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )

    print("\n--- Memulai Proses Pelatihan Assertion ---")
    trainer.train()

    print("\n--- Evaluasi pada Test Set (Data Uji Independen) ---")
    test_results = trainer.evaluate(test_dataset)
    print("\nHasil Evaluasi Akhir:")
    for k, v in test_results.items():
        if isinstance(v, float):
            print(f"  {k:20s}: {v:.4f}")

    print(f"\nMenyimpan model terbaik ke: {args.output}...")
    model.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)

    report_file = args.output / "eval_report.json"
    report_file.write_text(json.dumps(test_results, indent=2), encoding="utf-8")
    print(f"Laporan metrik tersimpan di: {report_file}")
    print("\n[SUKSES] Pelatihan IndoBERT Deteksi Negasi selesai dan siap diintegrasikan!")


if __name__ == "__main__":
    main()
