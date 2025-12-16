#!/usr/bin/env bash
# scripts/run_all.sh
#
# Project 03 — Full Cloud Pipeline Runner (AUTHORITATIVE)
#
# Usage:
#   ./run_all.sh <sam-packaging-bucket>
#
set -euo pipefail

# ------------------------------------------------------------
# Resolve paths
# ------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

CLOUD_DIR="$PROJECT_ROOT/cloud"
CLOUD_GEN="$CLOUD_DIR/generated"
EVIDENCE_DIR="$PROJECT_ROOT/evidence"

# ------------------------------------------------------------
# Runtime inputs
# ------------------------------------------------------------
PACKAGING_BUCKET="${1:-}"
PROFILE="${AWS_PROFILE:-deploy-ci}"
REGION="${AWS_REGION:-eu-west-1}"
STACK_NAME="project-03-public-health-datalake"

# ------------------------------------------------------------
# Hard validation
# ------------------------------------------------------------
[[ -z "$PACKAGING_BUCKET" ]] && {
  echo "ERROR: Packaging bucket required"
  echo "Usage: ./run_all.sh <sam-packaging-bucket>"
  exit 1
}

echo "Validating SAM packaging bucket: $PACKAGING_BUCKET"
aws s3api head-bucket \
  --bucket "$PACKAGING_BUCKET" \
  --profile "$PROFILE" \
  --region "$REGION" >/dev/null

# ------------------------------------------------------------
# Step 0 — Render templates
# ------------------------------------------------------------
echo
echo "STEP 0 — Rendering cloud templates"
"$CLOUD_DIR/bootstrap/envsubst-wrap.sh"

[[ -f "$CLOUD_GEN/templates/template.yml" ]] || {
  echo "ERROR: rendered SAM template missing"
  exit 1
}

mkdir -p "$EVIDENCE_DIR"/{athena,dashboard,deployment}

echo
echo "Using configuration:"
echo "  Stack            : $STACK_NAME"
echo "  Region           : $REGION"
echo "  Profile          : $PROFILE"
echo "  Packaging bucket : s3://$PACKAGING_BUCKET"
echo

# ------------------------------------------------------------
# Step 1 — SAM BUILD (MANDATORY)
# ------------------------------------------------------------
echo "STEP 1 — Building Lambda artifacts"

rm -rf .aws-sam
sam build \
  --template-file "$CLOUD_GEN/templates/template.yml" \
  --region "$REGION" \
  --profile "$PROFILE"

# HARD ASSERTIONS — NO FALSE SUCCESS
[[ -d ".aws-sam/build/IngestFunction" ]] || {
  echo "ERROR: IngestFunction build artifact missing"
  exit 1
}

[[ -d ".aws-sam/build/TransformFunction" ]] || {
  echo "ERROR: TransformFunction build artifact missing"
  exit 1
}

echo "✔ SAM build verified"
echo

# ------------------------------------------------------------
# Step 2 — SAM DEPLOY
# ------------------------------------------------------------
echo "STEP 2 — Deploying stack"

sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset \
  --profile "$PROFILE" \
  --s3-bucket "$PACKAGING_BUCKET"

echo "✔ Stack deployed"
echo

# ------------------------------------------------------------
# Step 3 — Resolve outputs
# ------------------------------------------------------------
get_output () {
  aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" \
    --output text \
    --region "$REGION" \
    --profile "$PROFILE"
}

INGEST_FN="$(get_output IngestLambda)"
[[ -n "$INGEST_FN" ]] || { echo "ERROR: IngestLambda missing"; exit 1; }

# ------------------------------------------------------------
# Step 4 — Trigger ingest
# ------------------------------------------------------------
echo "STEP 4 — Running ingest Lambda"

aws lambda invoke \
  --function-name "$INGEST_FN" \
  --payload '{}' \
  --region "$REGION" \
  --profile "$PROFILE" \
  /tmp/ingest-response.json >/dev/null

sleep 30
echo

# ------------------------------------------------------------
# Step 5 — Athena repair
# ------------------------------------------------------------
echo "STEP 5 — Repairing Athena partitions"
"$SCRIPT_DIR/athena/repair_partitions.sh"
echo

# ------------------------------------------------------------
# Step 6 — Run Athena queries
# ------------------------------------------------------------
echo "STEP 6 — Running Athena queries"
"$SCRIPT_DIR/athena/run_queries.sh"
echo

# ------------------------------------------------------------
# Step 7 — Build dashboard
# ------------------------------------------------------------
echo "STEP 7 — Building dashboard"
python src/dashboard/build.py
echo

# ------------------------------------------------------------
# Step 8 — Evidence
# ------------------------------------------------------------
echo "STEP 8 — Capturing deployment evidence"
"$SCRIPT_DIR/evidence/capture_deployment.sh"

echo
echo "PIPELINE COMPLETE"
