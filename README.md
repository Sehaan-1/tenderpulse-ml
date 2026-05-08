# tenderpulse-ml

Machine learning pipeline for classifying Indian government e-tender data from eProcure.

## Status

| Component | Status | Details |
|-----------|--------|---------|
| Title extraction | ✅ Done | `extract_title()` — right-to-left bracket matching, preserves nested brackets |
| PII scanner | ✅ Done | `scripts/check_pii.py` — gates any data/enriched/ commit |
| EDA | ✅ Done | `notebooks/01_eda.ipynb` — 769 tenders, 0% Hindi, 0% extraction failures |
| Model selection | ✅ Done | `notebooks/02_model_selection.ipynb` — BART wins 4/5 vs mDeBERTa 3/5 |
| Classification pipeline | ✅ Done | `src/classify.py` — BART zero-shot offline, ~20 min for 769 records |

## Quick Start

```bash
# Install dependencies
make install

# Run tests
make test

# Export HuggingFace model to run classification offline
python scripts/export_model.py

# Run zero-shot classification (produces data/enriched/tenders_enriched.jsonl)
make classify

# Check classification output step-by-step without writing
make classify-dry

# Run PII scan
python scripts/check_pii.py data/raw/tenders.jsonl

# Open EDA notebook
jupyter lab notebooks/01_eda.ipynb

# Open model selection notebook
jupyter lab notebooks/02_model_selection.ipynb
```

## Project Structure

```
tenderpulse-ml/
├── src/
│   ├── __init__.py
│   ├── title_cleaner.py         # Title extraction heuristics
│   ├── labels.py                # Zero-shot candidate labels
│   └── classify.py              # Classification pipeline
├── tests/
│   ├── test_title_cleaner.py    # 21 test cases for title extraction
│   └── test_classify.py         # 18 test cases for classification
├── scripts/
│   ├── check_pii.py             # PII scanner
│   └── export_model.py          # Export HF models for offline use
├── notebooks/
│   ├── 00_title_cleaning.ipynb  # Phase 1 validation: 50 before/after examples
│   ├── 01_eda.ipynb             # Data quality: 769 tender records
│   └── 02_model_selection.ipynb # BART vs mDeBERTa benchmark
├── data/
│   └── raw/
│       └── tenders.jsonl        # 769 real eProcure records
├── models/                      # Contains saved BART model for offline use
│   └── bart-large-mnli/
│       ├── config.json
│       ├── model.safetensors
│       ├── tokenizer.json
│       └── tokenizer_config.json
├── requirements.txt
├── Makefile
└── README.md
```

## Classification Pipeline

`tenderpulse-ml` uses **BART-large-mnli zero-shot classification** to assign one of three high-level categories to each tender:

| Category | Description |
|----------|-------------|
| **Goods** | Physical items, equipment, supplies |
| **Services** | Maintenance, consultancy, operations, support |
| **Works** | Construction, renovation, civil/electrical works |

Process per record:
1. Clean the raw title using `extract_title()`
2. Run the locally stored BART model offline
3. Write `predicted_category` and `category_confidence` into the JSONL

```bash
# First time only: export the model to run offline entirely
python scripts/export_model.py

# Run the full classification
make classify

# Output
# → data/enriched/tenders_enriched.jsonl
```

The model is loaded once and reused for all 769 records to avoid repeated overhead.

## Title Extraction

`extract_title()` in `src/title_cleaner.py` parses eProcure's `[title] [ref]` format:

- **Last** outermost `[...]` from the right = reference number
- Everything before it (including nested brackets) = title
- Returns `(title: str, ref: str | None)`
- Handles: missing ref, dimensions `[2.5m x 1.5m]`, org abbreviations `[DRDO]`, Hindi

## Model Selection Decision

Benchmarked `facebook/bart-large-mnli` vs `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` on 5 manually annotated ground-truth records across Construction and Maintenance categories.

| Model | Score | Notes |
|-------|-------|-------|
| **facebook/bart-large-mnli** | **4/5** | Selected |
| MoritzLaurer/mDeBERTa-v3-base-mnli-xnli | 3/5 | Multilingual advantage unused (0% Hindi in current sample) |

Decision rationale: BART scored strictly higher; mDeBERTa's multilingual capacity is not needed for the current dataset.

## License

Proprietary – Internal use only.