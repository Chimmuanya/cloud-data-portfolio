#!/usr/bin/env bash
# scripts/run_local_simulation.sh
# Developer-only LOCAL SIMULATION (locked environment)

set -euo pipefail



PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# ------------------------------------------------------------------
# Local filesystem prep (NO PATH EXPORTS)
# ------------------------------------------------------------------
LOCAL_RUN_ROOT="$PROJECT_ROOT/local_run"


# ------------------------------------------------------------------
# Runtime mode + imports
# ------------------------------------------------------------------
export MODE=LOCAL
export PYTHONPATH="$PROJECT_ROOT/src:$PROJECT_ROOT/local_run/src"



echo "Project Root: $PROJECT_ROOT"

echo "Python path: $PYTHONPATH"
# ------------------------------------------------------------------
# Ensure local virtual environment exists
# ------------------------------------------------------------------
VENV="$PROJECT_ROOT/local_run/.local_venv"

if [[ ! -d "$VENV" ]]; then
  echo "XXX Virtualenv not found at $VENV"
  echo "   Create it first (recommended):"
  echo "   python3 -m venv local_run/.local_venv"
  exit 1
fi

source "$VENV/bin/activate"

# ------------------------------------------------------------------
# Install locked local dependencies
# ------------------------------------------------------------------
LOCKFILE="$PROJECT_ROOT/local_run/requirements.local.lock"

if [[ ! -f "$LOCKFILE" ]]; then
  echo "XXX Lockfile not found: $LOCKFILE"
  echo "   Generate it with:"
  echo "   pip-compile local_run/requirements.local.txt"
  exit 1
fi

echo "> Installing locked local dependencies"
pip install --quiet --requirement "$LOCKFILE"

# ------------------------------------------------------------------
# Local filesystem prep (NO PATH EXPORTS)
# ------------------------------------------------------------------
LOCAL_RUN_ROOT="$PROJECT_ROOT/local_run"

mkdir -p \
  "$LOCAL_RUN_ROOT/local_data/raw" \
  "$LOCAL_RUN_ROOT/local_data/clean" \
  "$LOCAL_RUN_ROOT/evidence/athena" \
  "$LOCAL_RUN_ROOT/evidence/dashboard"

# ------------------------------------------------------------------
# Pipeline execution
# ------------------------------------------------------------------
echo ">> 1. Ingest (local simulation)"
python src/ingest/app.py

echo ">> 2. Transform (local simulation)"
python src/etl/normalize_healthdata.py

echo ">> 3. Analytics (athena_runner → DuckDB)"
python -c "from athena_runner.runner import run_all; run_all()"

echo ">> 4. Build dashboard"
python src/dashboard/build.py

echo ">> 5. Evidence manifest"
python src/evidence/write_evidence_manifest.py

echo "---- LOCAL SIMULATION COMPLETE ----"
