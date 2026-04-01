# Makefile for sparse-hate-explain
PYTHON := .venv/bin/python
UV := uv

.PHONY: install install-dev lint typecheck test clean phase0 validate-phase1 phase1 validate-train submit-wave1 submit-wave2

install:
	$(UV) venv
	$(UV) pip install -e .

install-dev:
	$(UV) venv
	$(UV) pip install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check src/ tests/ run_experiment.py

typecheck:
	$(PYTHON) -m mypy src/

test:
	$(PYTHON) -m pytest tests/ -v

# Phase 0: data analysis (no GPU required, ~5 min)
phase0:
	$(PYTHON) scripts/phase0_data_analysis.py

# Pre-submission validation for Phase 1 (imports, init, weight loading, dry-run)
validate-phase1:
	$(PYTHON) scripts/validate_phase1.py

# Phase 1: head importance scoring — validates first, then submits to SLURM
phase1: validate-phase1
	sbatch scripts/phase1_slurm.sh

# Pre-submission validation for training scripts (Wave 1 / Wave 2)
validate-train:
	$(PYTHON) scripts/validate_train.py

# Wave 1: M0+M1 and M3+M4b — validates first, then submits (requires Gate G1 pass)
submit-wave1: validate-train
	sbatch scripts/train.sh --conditions M0 M1
	sbatch scripts/train.sh --conditions M3 M4b

# Wave 2: ablations — validates first, then submits (requires Gate G2 pass)
submit-wave2: validate-train
	sbatch scripts/train.sh --conditions M2 M4a
	sbatch scripts/train.sh --conditions M4c M5
	sbatch scripts/train.sh --conditions M6 M7

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete
	rm -rf .mypy_cache .ruff_cache htmlcov .coverage
