"""
src/common/config.py

Central configuration for Project 3.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────
# Execution mode & Context
# ─────────────────────────────────────────────────────────────
MODE = os.getenv("MODE", "LOCAL").upper()
IS_LOCAL = MODE == "LOCAL"
IS_CLOUD = MODE == "CLOUD"

# Detect if we are inside an AWS Lambda environment
IS_LAMBDA = "AWS_LAMBDA_FUNCTION_NAME" in os.environ

def get_env(name: str, default: Optional[str] = None) -> str:
    """Fetch environment variable or fail fast."""
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

# ─────────────────────────────────────────────────────────────
# Filesystem Paths (Fixed for Lambda)
# ─────────────────────────────────────────────────────────────

# RULE: Lambda can ONLY write to /tmp.
# We use /tmp/data and /tmp/evidence when in the cloud.
if IS_LAMBDA:
    BASE_DATA_PATH = Path("/tmp") / "data"
    BASE_EVIDENCE_PATH = Path("/tmp") / "evidence"
else:
    # Local Fedora development paths
    BASE_DATA_PATH = Path("data")
    BASE_EVIDENCE_PATH = Path(os.getenv("EVIDENCE_DIR", Path.cwd() / "evidence"))

# Data Subdirectories
LOCAL_RAW_DIR = BASE_DATA_PATH / "raw"
LOCAL_CLEAN_DIR = BASE_DATA_PATH / "clean"

# Evidence Subdirectories
ATHENA_EVIDENCE_DIR = BASE_EVIDENCE_PATH / "athena"
DASHBOARD_EVIDENCE_DIR = BASE_EVIDENCE_PATH / "dashboard"

# Create directories (This now works in Lambda because they are under /tmp)
for directory in [LOCAL_RAW_DIR, LOCAL_CLEAN_DIR, ATHENA_EVIDENCE_DIR, DASHBOARD_EVIDENCE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Cloud Configuration (Buckets & Prefixes)
# ─────────────────────────────────────────────────────────────

# FIX: Avoid NameError by fetching the bucket name from Environment Variables
# which you already set in your template.yml
RAW_BUCKET = os.getenv("RAW_BUCKET")
CLEAN_BUCKET = os.getenv("CLEAN_BUCKET")
EVIDENCE_BUCKET = os.getenv("EVIDENCE_BUCKET")

# # If you still want to build it dynamically, ensure AWS_ACCOUNT_ID is fetched:
# AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "123456789512")
# ATHENA_OUTPUT_BUCKET = EVIDENCE_BUCKET or f"{AWS_ACCOUNT_ID}-project03-evidence"

ATHENA_DATABASE = "project03_db"
ATHENA_OUTPUT_PREFIX = "athena-results"

# Prefixes normalized
RAW_PREFIX = os.getenv("RAW_PREFIX", "public-health/raw").strip("/") + "/"
CLEAN_PREFIX = os.getenv("CLEAN_PREFIX", "public-health/clean").strip("/") + "/"

ETL_MANIFEST_KEY = os.getenv(
    "ETL_MANIFEST_KEY",
    f"{CLEAN_PREFIX}manifest/etl_manifest.json",
)
