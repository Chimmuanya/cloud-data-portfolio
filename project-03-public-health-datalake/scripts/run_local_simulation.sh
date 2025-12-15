#!/usr/bin/env bash
# scripts/run_local_simulation.sh
# Developer-only LOCAL SIMULATION

set -euo pipefail

export MODE=LOCAL
export PYTHONPATH="$(pwd)/src"

export LOCAL_RAW_DIR="local_data/raw"
export LOCAL_CLEAN_DIR="local_data/clean"
export ATHENA_EVIDENCE_DIR="evidence/athena"

mkdir -p "$LOCAL_RAW_DIR" "$LOCAL_CLEAN_DIR" "$ATHENA_EVIDENCE_DIR"

echo "▶ 1. Ingest (local simulation)"
python src/ingest/app.py

echo "▶ 2. Transform (local simulation)"
python src/etl/normalize_healthdata.py

echo "▶ 3. SQL analytics (DuckDB)"
python scripts/athena/run_queries_local.py

echo "▶ 4. Build dashboard"
python src/dashboard/build.py

echo "✅ LOCAL SIMULATION COMPLETE"
