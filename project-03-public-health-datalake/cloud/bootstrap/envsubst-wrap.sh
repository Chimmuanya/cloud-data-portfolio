#!/usr/bin/env bash
# cloud/bootstrap/envsubst.sh
#
# PURPOSE:
# Render cloud infrastructure templates into cloud/generated/
# using variables from a .env file.
#
# SCOPE:
# - ONLY cloud/templates/, cloud/policies/, cloud/sql/
# - NEVER scripts/
# - NEVER control-flow logic
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

CLOUD_DIR="$PROJECT_ROOT/cloud"
SRC_DIRS=(
  "$CLOUD_DIR/templates"
  "$CLOUD_DIR/policies"
  "$CLOUD_DIR/sql"
)
OUT_DIR="$CLOUD_DIR/generated"

ENV_FILE="${1:-$PROJECT_ROOT/.env}"

# -------------------------
# Load environment
# -------------------------
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env file not found: $ENV_FILE" >&2
  exit 1
fi

set -o allexport
source "$ENV_FILE"
set +o allexport

: "${ACCOUNT_ID:?ACCOUNT_ID is required}"
: "${AWS_REGION:=eu-west-1}"
: "${PACKAGING_BUCKET:?PACKAGING_BUCKET is required}"

echo "Rendering cloud templates"
echo "Project root : $PROJECT_ROOT"
echo "Env file     : $ENV_FILE"
echo "Output dir   : $OUT_DIR"
echo

# -------------------------
# Prepare output
# -------------------------
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# Variables allowed in substitution
ENV_VARS='
$ACCOUNT_ID
$AWS_REGION
$REGION
$PACKAGING_BUCKET
$RAW_BUCKET
$CLEAN_BUCKET
$ATHENA_RESULTS_BUCKET
$RAW_PREFIX
$CLEAN_PREFIX
$ATHENA_OUTPUT_S3
$DATABASE
$PROJECT_NAME
'

# -------------------------
# Render loop
# -------------------------
for SRC in "${SRC_DIRS[@]}"; do
  [[ -d "$SRC" ]] || continue

  REL="$(basename "$SRC")"
  DEST="$OUT_DIR/$REL"
  mkdir -p "$DEST"

  echo "→ Rendering $REL/"

  find "$SRC" -type f | while read -r file; do
    out="$DEST/${file#$SRC/}"
    mkdir -p "$(dirname "$out")"
    envsubst "$ENV_VARS" < "$file" > "$out"
    echo "   rendered: $REL/${file#$SRC/}"
  done
done

echo
echo "Cloud templates rendered successfully."
echo "Generated files live in: cloud/generated/"
