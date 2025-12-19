"""
src/common/config.py
Central configuration for Project 3.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────
# 1. Execution mode & Context
# ─────────────────────────────────────────────────────────────
MODE = os.getenv("MODE", "LOCAL").upper()
IS_LOCAL = MODE == "LOCAL"
IS_CLOUD = MODE == "CLOUD"
AWS_REGION = os.environ.get('AWS_REGION', 'eu-west-1')
IS_LAMBDA = "AWS_LAMBDA_FUNCTION_NAME" in os.environ

def get_env(name: str, default: Optional[str] = None) -> str:
    """Fetch environment variable or fail fast."""
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

# ─────────────────────────────────────────────────────────────
# 2. Cloud Configuration (Buckets & Prefixes)
# ─────────────────────────────────────────────────────────────
# FIX: Use get_env() for buckets so Lambda fails with a clear error
# if the environment variables are not set in the AWS Console.
if IS_CLOUD or IS_LAMBDA:
    RAW_BUCKET = get_env("RAW_BUCKET").lower()
    CLEAN_BUCKET = get_env("CLEAN_BUCKET").lower()
    EVIDENCE_BUCKET = get_env("EVIDENCE_BUCKET").lower()
else:
    # Allow empty strings for local development if not using S3
    RAW_BUCKET = os.getenv("RAW_BUCKET", "").lower()
    CLEAN_BUCKET = os.getenv("CLEAN_BUCKET", "").lower()
    EVIDENCE_BUCKET = os.getenv("EVIDENCE_BUCKET", "").lower()

ATHENA_DATABASE = "project03_db"
ATHENA_OUTPUT_PREFIX = "athena-results"
ATHENA_OUTPUT_BUCKET = EVIDENCE_BUCKET

# FIX: Construct path only if bucket exists to prevent "s3:///..."
if ATHENA_OUTPUT_BUCKET:
    ATHENA_OUTPUT_PATH = f"s3://{ATHENA_OUTPUT_BUCKET}/{ATHENA_OUTPUT_PREFIX}/"
else:
    ATHENA_OUTPUT_PATH = ""

RAW_PREFIX = os.getenv("RAW_PREFIX", "public-health/raw").strip("/") + "/"
CLEAN_PREFIX = os.getenv("CLEAN_PREFIX", "public-health/clean").strip("/") + "/"

ETL_MANIFEST_KEY = os.getenv(
    "ETL_MANIFEST_KEY",
    f"{CLEAN_PREFIX}manifest/etl_manifest.json",
)

# ─────────────────────────────────────────────────────────────
# 3. Filesystem Paths (Lambda /tmp vs Local)
# ─────────────────────────────────────────────────────────────
if IS_LAMBDA:
    BASE_DATA_PATH = Path("/tmp") / "data"
    BASE_EVIDENCE_PATH = Path("/tmp") / "evidence"
else:
    BASE_DATA_PATH = Path("data")
    BASE_EVIDENCE_PATH = Path(os.getenv("EVIDENCE_DIR", Path.cwd() / "evidence"))

LOCAL_DATA_DIR = BASE_DATA_PATH
LOCAL_RAW_DIR = BASE_DATA_PATH / "raw"
LOCAL_CLEAN_DIR = BASE_DATA_PATH / "clean"

ATHENA_EVIDENCE_DIR = BASE_EVIDENCE_PATH / "athena"
DASHBOARD_EVIDENCE_DIR = BASE_EVIDENCE_PATH / "dashboard"

# Ensure directories exist
for directory in [LOCAL_RAW_DIR, LOCAL_CLEAN_DIR, ATHENA_EVIDENCE_DIR, DASHBOARD_EVIDENCE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
