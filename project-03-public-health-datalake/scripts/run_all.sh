#!/usr/bin/env bash
# scripts/run_all.sh
#
# Project 03 — Full pipeline runner
# Consumes ONLY cloud/generated/
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

CLOUD_GEN="$PROJECT_ROOT/cloud/generated"
EVIDENCE_DIR="$PROJECT_ROOT/evidence"

PROFILE="${AWS_PROFILE:-deploy-ci}"
REGION="${AWS_REGION:-eu-west-1}"
STACK_NAME="project-03-public-health-datalake"

# -------------------------
# Safety checks
# -------------------------
echo "Validating generated cloud artifacts..."

[[ -d "$CLOUD_GEN" ]] || {
  echo "ERROR: cloud/generated/ not found."
  echo "Run cloud/bootstrap/envsubst.sh first."
  exit 1
}

[[ -f "$CLOUD_GEN/templates/template.yml" ]] || {
  echo "ERROR: Generated SAM template missing."
  exit 1
}

mkdir -p "$EVIDENCE_DIR/athena" "$EVIDENCE_DIR/dashboard"

echo "Using:"
echo "  Profile : $PROFILE"
echo "  Region  : $REGION"
echo "  Stack   : $STACK_NAME"
echo

# -------------------------
# 1. Deploy infrastructure
# -------------------------
echo "STEP 1 — Deploying CloudFormation stack"

sam deploy \
  --template-file "$CLOUD_GEN/templates/template.yml" \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset \
  --profile "$PROFILE"

echo "✔ Stack deployed"
echo

# -------------------------
# 2. Resolve stack outputs
# -------------------------
echo "STEP 2 — Resolving stack outputs"

get_output () {
  aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" \
    --output text \
    --region "$REGION" \
    --profile "$PROFILE"
}

INGEST_FN="$(get_output IngestLambda)"

[[ -n "$INGEST_FN" ]] || {
  echo "ERROR: IngestLambda not found"
  exit 1
}

echo "✔ Ingest Lambda: $INGEST_FN"
echo

# -------------------------
# 3. Run ingest
# -------------------------
echo "STEP 3 — Running ingest Lambda"

aws lambda invoke \
  --function-name "$INGEST_FN" \
  --payload '{}' \
  --region "$REGION" \
  --profile "$PROFILE" \
  /tmp/ingest-response.json > /dev/null

echo "✔ Ingest triggered"
echo "Waiting 30s for raw → clean pipeline..."
sleep 30
echo

# -------------------------
# 4. Repair Athena partitions (AUTOMATED)
# -------------------------
echo "STEP 4 — Repairing Athena partitions"

"$SCRIPT_DIR/athena/repair_partitions.sh"

echo "✔ Athena partitions repaired"
echo

# -------------------------
# 5. Run Athena queries
# -------------------------
echo "STEP 5 — Running Athena queries"

"$SCRIPT_DIR/athena/run_queries.sh"

echo "✔ Athena queries complete"
echo

# -------------------------
# 6. Build dashboard
# -------------------------
echo "STEP 6 — Building dashboard"

python src/dashboard/build.py

echo "✔ Dashboard built"
echo

# -------------------------
# 7. Capture evidence
# -------------------------
echo "STEP 7 — Capturing evidence"

"$SCRIPT_DIR/evidence/capture_deployment.sh"

echo
echo "PIPELINE COMPLETE ✅"
echo "Evidence written to: evidence/"
