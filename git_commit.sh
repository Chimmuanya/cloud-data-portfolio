#!/usr/bin/env bash
set -euo pipefail

echo "================================================="
echo " Project 03 — Capture Stabilization & Hardening"
echo "================================================="
echo

# Ensure we are in a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ Not inside a git repository."
  exit 1
fi

# Show current status
echo "🔍 Current git status:"
git status --short
echo

read -p "Proceed to stage ALL changes shown above? [y/N]: " CONFIRM
if [[ "${CONFIRM,,}" != "y" ]]; then
  echo "Aborted."
  exit 0
fi

# Stage everything
echo
echo "📦 Staging all changes..."
git add -A

echo
echo "📋 Staged files:"
git diff --cached --name-status
echo

# Commit message template
echo "📝 Opening commit message editor..."
echo
echo "Suggested commit message (you can edit freely):"
echo "-------------------------------------------------"
cat <<'EOF'
feat(project03): stabilize full cloud pipeline and dashboard generation

- Fixed Lambda read-only filesystem issues via /tmp redirection
- Hardened ingest, ETL, Athena runner, and dashboard paths
- Added Parquet engine (pyarrow) and S3 key decoding
- Resolved CloudFormation circular dependencies
- Added Athena WorkGroup + polling safeguards
- Ensured SQL files are packaged and discoverable in Lambda
- Optimized Plotly chart generation for memory efficiency
- Cleaned CloudWatch logging (Lambda-aware formatting)
- Added LOCAL-mode integration test for ingest layer
- Documented external IAM / AWS behavior inline for auditability

EOF
echo "-------------------------------------------------"
echo

git commit

# Optional push
echo
read -p "🚀 Push commit to origin/main now? [y/N]: " PUSH_CONFIRM
if [[ "${PUSH_CONFIRM,,}" == "y" ]]; then
  git push origin main
  echo "✅ Pushed successfully."
else
  echo "ℹ️ Commit created locally. Push when ready."
fi

echo
echo "🎉 Deployment stabilization snapshot complete."
