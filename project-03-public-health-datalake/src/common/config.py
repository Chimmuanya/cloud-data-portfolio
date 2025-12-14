"""
src/common/config.py

Central configuration for Project 3.
Used by ingest, ETL, dashboard, and scripts.
"""

import os
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────
# Core helper
# ─────────────────────────────────────────────────────────────

def get_env(name: str, default: Optional[str] = None) -> str:
    """
    Fetch environment variable or fail fast.
    """
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


# ─────────────────────────────────────────────────────────────
# Runtime context
# ─────────────────────────────────────────────────────────────

AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")
IS_LAMBDA = "AWS_LAMBDA_FUNCTION_NAME" in os.environ


# ─────────────────────────────────────────────────────────────
# Buckets (used by ingest + ETL)
# ─────────────────────────────────────────────────────────────

RAW_BUCKET = os.environ.get("RAW_BUCKET")
CLEAN_BUCKET = os.environ.get("CLEAN_BUCKET")

RAW_PREFIX = (
    os.environ.get("RAW_PREFIX", "public-health/raw/")
    .strip("/") + "/"
)

CLEAN_PREFIX = (
    os.environ.get("CLEAN_PREFIX", "public-health/clean/")
    .strip("/") + "/"
)


# ─────────────────────────────────────────────────────────────
# Evidence paths (used by dashboard + queries)
# ─────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(
    os.environ.get("PROJECT_ROOT", Path.cwd())
)

EVIDENCE_DIR = Path(
    os.environ.get("EVIDENCE_DIR", PROJECT_ROOT / "evidence")
)

ATHENA_EVIDENCE_DIR = EVIDENCE_DIR / "athena"
DASHBOARD_EVIDENCE_DIR = EVIDENCE_DIR / "dashboard"


# ─────────────────────────────────────────────────────────────
# ETL manifest
# ─────────────────────────────────────────────────────────────

ETL_MANIFEST_KEY = os.environ.get(
    "ETL_MANIFEST_KEY",
    f"{CLEAN_PREFIX}manifest/etl_manifest.json"
)
