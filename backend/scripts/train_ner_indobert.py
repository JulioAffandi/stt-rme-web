"""Skrip pelatihan (fine-tuning) model IndoBERT untuk Named Entity Recognition (NER) medis.

Menggunakan backbone: `indobenchmark/indobert-base-p1`
Input dataset: `data/nlp_datasets/ner_assertion.json` (2.397 kalimat, 6.037 entitas)
Skema label: BIO (13 kelas)
Evaluasi: `seqeval` (chunk-level entity evaluation)

Output:
- Model checkpoint tersimpan di `backend/models_store/ner_indobert/`
- Laporan evaluasi lengkap tersimpan di `backend/models_store/ner_indobert/eval_report.json`
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATASET = PROJECT_ROOT / "data" / "nlp_datasets" / "ner_assertion.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "backend" / "models_store" / "ner_indobert"
DEFAULT_MODEL_NAME = "indobenchmark/indobert-base-p1"

LABELS = [
    "O",
    "B-GEJALA",
    "I-GEJALA",
    "B-TANDA",
    "I-TANDA",
    "B-DIAGNOSIS",
    "I-DIAGNOSIS",
    "B-OBAT",
    "I-OBAT",
    "B-TINDAKAN",
    "I-TINDAKAN",
    "B-PENUNJANG",
    "I-PENUNJANG",
]
LABEL2ID = {label: i for i, label in enumerate(LABELS)}
ID2LABEL = {i: label for i, label in enumerate(LABELS)}


def compute_metrics_fn(p):
    from seqeval.metrics import classification_report, f1_score, precision_score, recall_score

    predictions, labels = p
    preds = np.argmax(predictions, axis=2)

    # Buang token khusus (-100)
    true_predictions = [
        [ID2LABEL[p_idx] for (p_idx, l_idx) in zip(prediction, label) if l_idx != -100]
        for prediction, label in zip(preds, labels)
    ]
    true_labels = [
        [ID2LABEL[l_idx] for (p_idx, l_idx) in zip(prediction, label) if l_idx != -100]
        for prediction, label in zip(preds, labels)
    ]

    p_score = precision_score(true_labels, true_predictions, zero_division=0)
    r_score = recall_score(true_labels, true_predictions, zero_division=0)
    f_score = f1_score(true_labels, true_predictions, zero_division=0)

    report_dict = classification_report(true_labels, true_predictions, output_dict=True, zero_division=0)

    results = {
        "precision": p_score,
        "recall": r_score,
        "f1": f_score,
    }

    # Tambahkan per-entity metrics
    for ent_type in ["GEJALA", "TANDA", "DIAGNOSIS", "OBAT", "TINDAKAN", "PENUNJANG"]:
        if ent_type in report_dict:
            results[f"f1_{ent_type}"] = report_dict[ent_type]["f1-score"]

    return results


def align_labels_with_tokens(tokenizer, sentence: str, entities: list[dict], max_len: int = 128):
    enc = tokenizer(
        sentence,
        truncation=True,
        max_length=max_len,
        padding="max_length",
        return_offsets_mapping=True,
        return_tensors="pt",
    )
    offsets = enc["offset_mapping"][0].tolist()

    tags = []
    for start, end in offsets:
        if start == end:
            tags.append(-100)
            continue

        token_tag = "O"
        for ent in entities:
            e_start, e_end, e_lbl = ent["start"], ent["end"], ent["label"]
            if start >= e_start and end <= e_end:
                if start == e_start:
                    token_tag = f"B-{e_lbl}"
                else:
                    token_tag = f"I-{e_lbl}"
                break
        tags.append(LABEL2ID.get(token_tag, 0))

    item = {
        "input_ids": enc["input_ids"][0],
        "attention_mask": enc["attention_mask"][0],
        "labels": np.array(tags, dtype=np.int64),
    }
    return item


def main() -> None:
    import torch
    from sklearn.model_selection import train_test_split
    from transformers import (
        AutoModelForTokenClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    parser = argparse.ArgumentParser(description="Fine-tune IndoBERT untuk NER Medis")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET, help="Path ke file dataset JSON")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_NAME, help="Pretrained model HF")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR, help="Folder output model")
    parser.add_argument("--epochs", type=int, default=4, help="Jumlah epoch pelatihan (default: 4)")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size (default: 16)")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate (default: 3e-5)")
    parser.add_argument("--max-len", type=int, default=128, help="Max sequence length (default: 128)")
    args = parser.parse_args()

    print("=" * 60)
    print("PELATIHAN MODEL INDOBERT UNTUK NER MEDIS (BIO TAGGING)")
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
    print(f"Total kalimat klinis: {len(raw_data)}")
    total_ents = sum(len(x.get("entities", [])) for x in raw_data)
    print(f"Total entitas klinis: {total_ents}")

    # Split dataset 80% Train, 10% Val, 10% Test
    train_data, temp_data = train_test_split(raw_data, test_size=0.20, random_state=42)
    val_data, test_data = train_test_split(temp_data, test_size=0.50, random_state=42)

    print(f"\nPembagian data:")
    print(f"  Train : {len(train_data)} kalimat")
    print(f"  Val   : {len(val_data)} kalimat")
    print(f"  Test  : {len(test_data)} kalimat")

    print(f"\nMemuat tokenizer: {args.model}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model)

    print("Melakukan alignment token dan membuat PyTorch Dataset...")

    class ClinicalNerDataset(torch.utils.data.Dataset):
        def __init__(self, records):
            self.items = []
            for r in records:
                item = align_labels_with_tokens(tokenizer, r["sentence"], r.get("entities", []), max_len=args.max_len)
                self.items.append(item)

        def __len__(self):
            return len(self.items)

        def __getitem__(self, idx):
            item = self.items[idx]
            return {
                "input_ids": item["input_ids"],
                "attention_mask": item["attention_mask"],
                "labels": torch.tensor(item["labels"], dtype=torch.long),
            }

    train_dataset = ClinicalNerDataset(train_data)
    val_dataset = ClinicalNerDataset(val_data)
    test_dataset = ClinicalNerDataset(test_data)

    print(f"Memuat model Token Classification: {args.model} ({len(LABELS)} labels)...")
    model = AutoModelForTokenClassification.from_pretrained(
        args.model,
        num_labels=len(LABELS),
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
        metric_for_best_model="f1",
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
        compute_metrics=compute_metrics_fn,
    )

    print("\n--- Memulai Proses Pelatihan NER ---")
    trainer.train()

    print("\n--- Evaluasi pada Test Set (Data Uji Independen) ---")
    test_results = trainer.evaluate(test_dataset)
    print("\nHasil Evaluasi Akhir (Chunk-Level SeqEval):")
    for k, v in test_results.items():
        if isinstance(v, float):
            print(f"  {k:20s}: {v:.4f}")

    print(f"\nMenyimpan model terbaik ke: {args.output}...")
    model.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)

    report_file = args.output / "eval_report.json"
    report_file.write_text(json.dumps(test_results, indent=2), encoding="utf-8")
    print(f"Laporan metrik tersimpan di: {report_file}")
    print("\n[SUKSES] Pelatihan IndoBERT NER Medis selesai dan siap diintegrasikan!")


if __name__ == "__main__":
    main()
