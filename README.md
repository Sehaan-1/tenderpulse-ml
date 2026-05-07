# tenderpulse-ml

Machine learning pipeline for classifying Indian government e-tender data from eProcure.

## Status

| Component | Status | Details |
|-----------|--------|---------|
| Title extraction | ✅ Done | `extract_title()` — right-to-left bracket matching, preserves nested brackets |
| PII scanner | ✅ Done | `scripts/check_pii.py` — gates any data/enriched/ commit |
| EDA | ✅ Done | `notebooks/01_eda.ipynb` — 769 tenders, 0% Hindi, 0% extraction failures |
| Model selection | ✅ Done | `notebooks/02_model_selection.ipynb` — BART wins 4/5 vs mDeBERTa 3/5 |
| Classification | — | Phase 3 pending |

## Quick Start

```bash
# Install dependencies
make install

# Run tests
make test

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
│   └── title_cleaner.py         # extract_title() heuristic
├── tests/
│   └── test_title_cleaner.py    # 21 test cases
├── scripts/
│   └── check_pii.py             # PII scanner (mobile, email, officer prefixes)
├── notebooks/
│   ├── 00_title_cleaning.ipynb  # Phase 1 validation: 50 before/after examples
│   ├── 01_eda.ipynb             # Data quality: 769 tender records
│   └── 02_model_selection.ipynb # BART vs mDeBERTa benchmark
├── data/
│   └── raw/
│       └── tenders.jsonl        # 769 real eProcure records
├── requirements.txt
├── Makefile
└── README.md
```

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