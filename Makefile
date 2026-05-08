.PHONY: install test classify classify-dry evaluate sanity clean lint format

PYTHON := python
PIP := pip

install:
	$(PIP) install -r requirements.txt

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/ scripts/

format:
	ruff format src/ tests/ scripts/

classify:
	python src/classify.py --input data/raw/tenders.jsonl --output data/enriched/tenders_enriched.jsonl

classify-dry:
	@echo "Dry run: would classify data/raw/tenders.jsonl -> data/enriched/tenders_enriched.jsonl"

evaluate:
	python notebooks/phase4_eval.py

sanity:
	python scripts/check_pii.py

clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
