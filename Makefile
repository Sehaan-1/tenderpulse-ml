.PHONY: install test classify eval clean lint format

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
	@echo "classify target is a stub for Phase 2+"

sanity:
	python scripts/check_pii.py

clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
