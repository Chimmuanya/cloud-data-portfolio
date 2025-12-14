#!/usr/bin/env bash
# scripts/athena/run_queries.sh
#
# Project 03 — Athena SQL Runner
#
# RESPONSIBILITY (STRICT):
# - Execute Athena SQL that has ALREADY been rendered
# - NEVER mutate SQL
# - NEVER substitute variables
#
# SOURCE OF TRUTH:
#   cloud/generated/sql/
#
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# Required environment
# ─────────────────────────────────────────────────────────────

: "${ATHENA_OUTPUT_S3:?Must set ATHENA_OUTPUT_S3 (s3://bucket/path/)}"
: "${DATABASE:=project03_db}"
: "${AWS_REGION:=eu-west-1}"
: "${AWS_PROFILE:=deploy-ci}"

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

SQL_ROOT="${ROOT_DIR}/cloud/generated/sql"
DDL_DIR="${SQL_ROOT}/ddl"
QUERY_DIR="${SQL_ROOT}/queries"
EVIDENCE_DIR="${ROOT_DIR}/evidence/athena"

mkdir -p "${EVIDENCE_DIR}"

command -v jq >/dev/null || {
  echo "jq is required" >&2
  exit 1
}

# ─────────────────────────────────────────────────────────────
# Safety checks
# ─────────────────────────────────────────────────────────────

[[ -d "$SQL_ROOT" ]] || {
  echo "ERROR: cloud/generated/sql not found"
  echo "Run cloud/bootstrap/envsubst.sh first"
  exit 1
}

[[ -d "$DDL_DIR" || -d "$QUERY_DIR" ]] || {
  echo "ERROR: No DDL or query SQL found in cloud/generated/sql"
  exit 1
}

# ─────────────────────────────────────────────────────────────
# Athena helpers
# ─────────────────────────────────────────────────────────────

run_sql_file () {
  local sqlfile="$1"
  local label="$2"

  echo "▶ Running: ${label}"

  local exec_id
  exec_id=$(aws athena start-query-execution \
    --query-string "$(cat "$sqlfile")" \
    --query-execution-context Database="$DATABASE" \
    --result-configuration OutputLocation="$ATHENA_OUTPUT_S3" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --output text)

  while true; do
    state=$(aws athena get-query-execution \
      --query-execution-id "$exec_id" \
      --region "$AWS_REGION" \
      --profile "$AWS_PROFILE" \
      | jq -r '.QueryExecution.Status.State')

    case "$state" in
      SUCCEEDED) break ;;
      FAILED|CANCELLED)
        echo "❌ Query failed: $label"
        aws athena get-query-execution \
          --query-execution-id "$exec_id" \
          --region "$AWS_REGION" \
          --profile "$AWS_PROFILE"
        exit 2 ;;
      *) sleep 2 ;;
    esac
  done

  local result_s3
  result_s3=$(aws athena get-query-execution \
    --query-execution-id "$exec_id" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    | jq -r '.QueryExecution.ResultConfiguration.OutputLocation')

  local out="${EVIDENCE_DIR}/${label}-${exec_id}.csv"
  aws s3 cp "$result_s3" "$out" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE"

  echo "✔ Saved → ${out}"
}

# ─────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────

case "${1:-help}" in

  ddl-run)
    echo "STEP — Running Athena DDLs"
    for f in "${DDL_DIR}"/*.sql; do
      run_sql_file "$f" "$(basename "$f" .sql)"
    done

    echo "STEP — Repairing partitions"
    aws athena start-query-execution \
      --query-string "MSCK REPAIR TABLE who_indicators" \
      --query-execution-context Database="$DATABASE" \
      --result-configuration OutputLocation="$ATHENA_OUTPUT_S3" \
      --region "$AWS_REGION" \
      --profile "$AWS_PROFILE" >/dev/null
    ;;

  run)
    q="${2:-}"
    [[ -z "$q" ]] && { echo "Specify query name (e.g. Query05)"; exit 1; }

    file=$(ls "${QUERY_DIR}/${q}"*.sql 2>/dev/null | head -n1)
    [[ -f "$file" ]] || { echo "Query not found: $q"; exit 1; }

    run_sql_file "$file" "$(basename "$file" .sql)"
    ;;

  run-all)
    for f in "${QUERY_DIR}"/*.sql; do
      run_sql_file "$f" "$(basename "$f" .sql)"
    done
    ;;

  *)
    echo "Usage:"
    echo "  run_queries.sh ddl-run"
    echo "  run_queries.sh run Query05"
    echo "  run_queries.sh run-all"
    ;;
esac
