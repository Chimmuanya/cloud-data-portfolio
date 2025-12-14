#!/usr/bin/env bash
# scripts/local/run_local_simulation.sh
#
# Developer-only LOCAL SIMULATION
# Faithfully mirrors cloud pipeline using DuckDB

set -euo pipefail

export MODE=local

export LOCAL_RAW_DIR="local_data/raw"
export LOCAL_CLEAN_DIR="local_data/clean"
export ATHENA_EVIDENCE_DIR="evidence/athena"

mkdir -p "$LOCAL_RAW_DIR" "$LOCAL_CLEAN_DIR" "$ATHENA_EVIDENCE_DIR"

echo "▶ 1. Ingest (local simulation)"
python src/ingest/app.py   # already supports local mode

echo "▶ 2. Transform (local simulation)"
python src/transform/app.py

echo "▶ 3. SQL analytics (DuckDB)"
python scripts/athena/run_queries_local.py

echo "▶ 4. Build dashboard"
python src/dashboard/build.py

echo "✅ LOCAL SIMULATION COMPLETE"
