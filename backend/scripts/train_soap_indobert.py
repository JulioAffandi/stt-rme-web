"""Skrip pelatihan (fine-tuning) model IndoBERT untuk klasifikasi kalimat SOAP.

Menggunakan backbone: `indobenchmark/indobert-base-p1`
Input dataset: `data/nlp_datasets/soap_classification.json` (2.397 kalimat)
Target kelas: 4 kelas (S, O, A, P)

Output:
- Model checkpoint tersimpan di `backend/models_store/soap_indobert/`
- Laporan metrik evaluasi lengkap (Accuracy, Precision, Recall, F1-Score per kelas)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATASET = PROJECT_ROOT / "data" / "nlp_datasets" / "soap_classification.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "backend" / "models_store" / "soap_indobert"
DEFAULT_MODEL_NAME = "indobenchmark/indobert-base-p1"

LABEL2ID = {"S": 0, "O": 1, "A": 2, "P": 3}
ID2LABEL = {0: "S", 1: "O", 2: "A", 3: "P"}


def check_dependencies() -> None:
    required = ["torch", "transformers", "sklearn", "pandas", "accelerate"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print("\n[PERINGATAN] Dependensi berikut belum terinstall:")
        print(f"  {', '.join(missing)}")
        print("\nSilakan install terlebih dahulu menggunakan perintah:")
        print("  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
        print("  pip install transformers datasets scikit-learn pandas accelerate")
        sys.exit(1)


def compute_metrics(eval_pred):
    from sklearn.metrics import accuracy_score, classification_report, precision_recall_fscore_support

    predictions, labels = eval_pred
    preds = np.argmax(predictions, axis=1)

    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="macro", zero_division=0)
    acc = accuracy_score(labels, preds)

    # Per-class metrics
    report = classification_report(
        labels,
        preds,
        target_names=["S (Subjective)", "O (Objective)", "A (Assessment)", "P (Plan)"],
        output_dict=True,
        zero_division=0,
    )

    metrics = {
        "accuracy": acc,
        "f1_macro": f1,
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_S": report["S (Subjective)"]["f1-score"],
        "f1_O": report["O (Objective)"]["f1-score"],
        "f1_A": report["A (Assessment)"]["f1-score"],
        "f1_P": report["P (Plan)"]["f1-score"],
    }
    return metrics


def main() -> None:
    check_dependencies()

    import pandas as pd
    import torch
    from sklearn.model_selection import train_test_split
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    parser = argparse.ArgumentParser(description="Fine-tune IndoBERT untuk SOAP")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET, help="Path ke file dataset JSON")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_NAME, help="Pretrained model HF")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR, help="Folder output model")
    parser.add_argument("--epochs", type=int, default=4, help="Jumlah epoch pelatihan (default: 4)")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size (default: 16)")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate (default: 3e-5)")
    parser.add_argument("--max-len", type=int, default=128, help="Max sequence length token (default: 128)")
    args = parser.parse_args()

    print("=" * 60)
    print("PELATIHAN MODEL INDOBERT UNTUK KLASIFIKASI SOAP")
    print("=" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device komputasi: {device.upper()}")
    if device == "cuda":
        print(f"Nama GPU: {torch.cuda.get_device_name(0)}")
        print(f"Total VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

    if not args.data.exists():
        print(f"ERROR: Dataset tidak ditemukan di {args.data}")
        sys.exit(1)

    # 1. Load Dataset
    print(f"\nMemuat dataset dari {args.data}...")
    raw_data = json.loads(args.data.read_text(encoding="utf-8"))
    df = pd.DataFrame(raw_data)
    df["label"] = df["soap"].map(LABEL2ID)
    df = df.dropna(subset=["sentence", "label"])
    df["label"] = df["label"].astype(int)

    print(f"Total data valid: {len(df)} kalimat")
    print("Distribusi per kelas:")
    for soap_char, soap_id in LABEL2ID.items():
        count = (df["label"] == soap_id).sum()
        pct = (count / len(df)) * 100
        print(f"  [{soap_char}] {soap_id}: {count} ({pct:.1f}%)")

    # 2. Stratified Train / Val / Test Split (80% / 10% / 10%)
    train_df, temp_df = train_test_split(df, test_size=0.20, random_state=42, stratify=df["label"])
    val_df, test_df = train_test_split(temp_df, test_size=0.50, random_state=42, stratify=temp_df["label"])

    print(f"\nPembagian data:")
    print(f"  Train : {len(train_df)} kalimat")
    print(f"  Val   : {len(val_df)} kalimat")
    print(f"  Test  : {len(test_df)} kalimat")

    # 3. Tokenizer & Dataset Class
    print(f"\nMemuat tokenizer: {args.model}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model)

    class ClinicalSoapDataset(torch.utils.data.Dataset):
        def __init__(self, texts, labels):
            self.encodings = tokenizer(
                texts,
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

    train_dataset = ClinicalSoapDataset(train_df["sentence"].tolist(), train_df["label"].tolist())
    val_dataset = ClinicalSoapDataset(val_df["sentence"].tolist(), val_df["label"].tolist())
    test_dataset = ClinicalSoapDataset(test_df["sentence"].tolist(), test_df["label"].tolist())

    # 4. Model Setup
    print(f"Memuat model klasifikasi: {args.model} (4 labels)...")
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model,
        num_labels=4,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True,
    )

    args.output.mkdir(parents=True, exist_ok=True)

    # 5. Training Arguments
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

    # 6. Mulai Fine-Tuning
    print("\n--- Memulai Proses Pelatihan ---")
    trainer.train()

    # 7. Evaluasi pada Test Set Independen
    print("\n--- Evaluasi pada Test Set (Data Uji Independen) ---")
    test_results = trainer.evaluate(test_dataset)
    print("\nHasil Evaluasi Akhir:")
    for k, v in test_results.items():
        if isinstance(v, float):
            print(f"  {k:20s}: {v:.4f}")

    # 8. Simpan Model Terbaik & Tokenizer
    print(f"\nMenyimpan model terbaik ke: {args.output}...")
    model.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)

    # Simpan laporan evaluasi ke JSON
    report_file = args.output / "eval_report.json"
    report_file.write_text(json.dumps(test_results, indent=2), encoding="utf-8")
    print(f"Laporan metrik tersimpan di: {report_file}")
    print("\n[SUKSES] Pelatihan IndoBERT SOAP Classifier selesai dan siap diintegrasikan!")


if __name__ == "__main__":
    main()
