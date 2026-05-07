# tenderpulse-ml

Machine learning pipeline for the TenderPulse project — extracting, cleaning and classifying Indian government e-tender data.

## Phase Status

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | **Done** | Title extraction heuristic + PII scanner |
| 2 | — | Classification model (mDeBERTa / BART) |
| 3 | — | Evaluation & metrics |

## Project Structure

```
tenderpulse-ml/
├── src/                     # Core Python modules
│   └── title_cleaner.py     # extract_title() heuristic
├── tests/                   # pytest suite
│   └── test_title_cleaner.py
├── scripts/                 # Utility scripts
│   └── check_pii.py         # PII scanner gate
├── notebooks/               # Jupyter notebooks
│   └── 00_title_cleaning.ipynb
├── data/
│   └── raw/
│       └── tenders.jsonl    # Source data (eProcure)
├── requirements.txt
├── Makefile
└── README.md
```

## Quick Start

```bash
# Install dependencies
make install

# Run tests
make test

# Run PII scan
python scripts/check_pii.py data/raw/tenders.jsonl

# Run notebook
jupyter lab notebooks/00_title_cleaning.ipynb
```

## Title Cleaner

The `extract_title()` function in `src/title_cleaner.py` extracts clean title and reference number from eProcure's `[title] [ref]` format.

**Rules:**
- Last outermost `[(.*?)]` from the **right** = reference number
- Everything before it (nested brackets preserved) = title
- Returns `(title: str, ref: str | None)`

## PII Scanner

`scripts/check_pii.py` scans JSONL files for:

- 10-digit Indian mobile numbers
- `+91` prefixes
- Landline patterns
- Email addresses
- Officer name prefixes (`Shri`, `Smt`, `Dr.`, `Er.`)

Run this before committing any `data/enriched/` files.

## License

Proprietary – Internal use only.
