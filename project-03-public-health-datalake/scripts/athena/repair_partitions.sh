#!/usr/bin/env bash
# scripts/athena/repair_partitions.sh
#
# Automatically repair Athena partitions for Project 3 tables
#
set -euo pipefail

DATABASE="${DATABASE:-project03_db}"
REGION="${AWS_REGION:-eu-west-1}"
PROFILE="${AWS_PROFILE:-deploy-ci}"
ATHENA_OUTPUT_S3="${ATHENA_OUTPUT_S3:?ATHENA_OUTPUT_S3 is required}"

TABLES=(
  who_indicators
  worldbank_indicators
  who_outbreaks
)

echo "Repairing Athena partitions"
echo "Database : $DATABASE"
echo "Region   : $REGION"
echo

for table in "${TABLES[@]}"; do
  echo "→ MSCK REPAIR TABLE ${DATABASE}.${table}"
  aws athena start-query-execution \
    --query-string "MSCK REPAIR TABLE ${DATABASE}.${table}" \
    --query-execution-context Database="$DATABASE" \
    --result-configuration OutputLocation="$ATHENA_OUTPUT_S3" \
    --region "$REGION" \
    --profile "$PROFILE" \
    >/dev/null
done

echo
echo "Partition repair triggered successfully."
