#!/usr/bin/env bash
# scripts/deploy/deploy_stack.sh
#
# Project 3 — CloudFormation / SAM Deployment
#
# Provisions the Public Health Data Lake infrastructure.

set -euo pipefail

# ─────────────────────────────────────────────────────────────
# Resolve paths
# ─────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

# ─────────────────────────────────────────────────────────────
# Load environment
# ─────────────────────────────────────────────────────────────

if [[ -f ".env" ]]; then
  echo "Loading variables from .env"
  export $(grep -v '^#' .env | xargs)
fi

# Required
: "${ACCOUNT_ID:?ACCOUNT_ID is required (12-digit AWS account ID)}"
: "${PACKAGING_BUCKET:?PACKAGING_BUCKET is required}"
: "${AWS_REGION:=eu-west-1}"

# Optional
STACK_NAME="${STACK_NAME:-project-03-public-health-datalake}"
DRY_RUN="${DRY_RUN:-false}"

echo "Deploying Project 3 — Public Health Data Lake"
echo "Account ID      : ${ACCOUNT_ID}"
echo "Region          : ${AWS_REGION}"
echo "Stack name      : ${STACK_NAME}"
echo "Packaging bucket: ${PACKAGING_BUCKET}"
echo "Dry run         : ${DRY_RUN}"
echo

# ─────────────────────────────────────────────────────────────
# Step 1: Render infrastructure template
# ─────────────────────────────────────────────────────────────

if [[ "$DRY_RUN" == "false" ]]; then
  echo "Rendering infrastructure template..."
  infra/bootstrap/envsubst-wrap.sh --env-file .env
else
  echo "DRY RUN: Would render infra template via envsubst"
fi

# ─────────────────────────────────────────────────────────────
# Step 2: SAM build & deploy
# ─────────────────────────────────────────────────────────────

if [[ "$DRY_RUN" == "false" ]]; then
  echo "Building Lambda artifacts..."
  sam build --use-container

  echo "Deploying stack..."
  sam deploy \
    --template-file infra/generated/template.yml \
    --stack-name "$STACK_NAME" \
    --s3-bucket "$PACKAGING_BUCKET" \
    --region "$AWS_REGION" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset

  echo
  echo "DEPLOYMENT SUCCESSFUL"
else
  echo "DRY RUN: Would run sam build && sam deploy"
fi

echo
echo "Deployment step complete."
