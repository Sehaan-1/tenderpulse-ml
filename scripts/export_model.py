"""Export Hugging Face model to local folder."""

import sys
from pathlib import Path

from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_NAME = "facebook/bart-large-mnli"
OUTPUT_DIR = "models/bart-large-mnli"

print(f"Downloading/exporting model: {MODEL_NAME} ...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

print(f"Saving to {OUTPUT_DIR} ...")
tokenizer.save_pretrained(OUTPUT_DIR)
model.save_pretrained(OUTPUT_DIR)

print("[OK] Export complete.")
print(f"  Saved {len(list(Path(OUTPUT_DIR).iterdir()))} files to {OUTPUT_DIR}")