# Scikit-TDA evaluation project — Makefile (blueprint Section 7)
# Execution order: verify -> e1 -> e2 -> e3 -> figures -> test
# (e3 generates the single-observer inspection MATERIALS from saved
#  results; the completed record is authored by hand and analyzed by
#  scripts/analyze_e3_inspection.py. No participant data exist.)
PYTHON ?= .venv/bin/python
PIP    ?= .venv/bin/pip

.PHONY: verify e1 e2 e3 figures test all env repro glue e3-analysis

env:
	python3.12 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt -r requirements-dev.txt
	@echo "Environment ready. Activate with: source .venv/bin/activate"

verify:
	$(PYTHON) scripts/verify_env.py

e1:
	$(PYTHON) scripts/run_e1_audit.py

e2:
	$(PYTHON) scripts/run_e2_sensitivity.py

e3:
	$(PYTHON) scripts/run_e3_readability.py

e3-analysis:
	$(PYTHON) scripts/analyze_e3_inspection.py

figures:
	$(PYTHON) src/figures.py --all

test:
	$(PYTHON) -m pytest tests/ -q

glue:
	$(PYTHON) scripts/count_glue_code.py

repro:
	bash scripts/clean_clone_test.sh

all: verify e1 e2 e3 figures test
