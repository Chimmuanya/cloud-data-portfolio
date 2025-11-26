#!/usr/bin/env bash
# scripts/atomic_commit.sh
# Usage:
#   ./scripts/atomic_commit.sh "type(scope): short message" [--sign]
# Example:
#   ./scripts/atomic_commit.sh "feat(serverless): add csv qc lambda"
set -euo pipefail

MSG="${1:-}"
if [ -z "$MSG" ]; then
  echo "Usage: $0 \"type(scope): short message\""
  exit 1
fi

# Stage all changes
git add -A

# Run tests if present (non-fatal)
if command -v pytest >/dev/null 2>&1; then
  echo "Running pytest..."
  pytest || echo "Tests failed — aborting commit" && exit 1
fi

# Commit atomically
git commit -m "$MSG"

