# --------------------------------------------------
# Project 03 — Local Development Workflow
# --------------------------------------------------

PROJECT_ROOT := $(shell pwd)
VENV := $(PROJECT_ROOT)/local_run/.venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

LOCAL_REQ := local_run/requirements.local.lock

.PHONY: help venv deps local-run clean

help:
	@echo ""
	@echo "Available targets:"
	@echo "  make venv        Create local virtual environment"
	@echo "  make deps        Install local dependencies"
	@echo "  make local-run   Run full LOCAL simulation pipeline"
	@echo "  make clean       Remove local virtual environment"
	@echo ""

# --------------------------------------------------
# Virtual environment
# --------------------------------------------------
venv:
	@test -d $(VENV) || python3.11 -m venv $(VENV)
	@echo "✔ Virtualenv ready at $(VENV)"

# --------------------------------------------------
# Dependencies
# --------------------------------------------------
deps: venv
	@$(PIP) install --upgrade pip
	@$(PIP) install -r $(LOCAL_REQ)
	@echo "✔ Local dependencies installed"

# --------------------------------------------------
# Full local simulation
# --------------------------------------------------
local-run: deps
	@echo "▶ Running LOCAL simulation"
	@MODE=LOCAL PYTHONPATH=$(PROJECT_ROOT)/src $(PYTHON) scripts/run_local_simulation.sh

# --------------------------------------------------
# Cleanup
# --------------------------------------------------
clean:
	rm -rf local_run/.venv
	@echo "✔ Local environment cleaned"
