"""
src/common/config.py

Central configuration for Project 3.

Single source of truth for:
- execution mode (LOCAL / CLOUD)
- AWS + local paths
- prefixes and manifests
- evidence outputs

Used by ingest, ETL, dashboard, and scripts.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────
# Execution mode
# ─────────────────────────────────────────────────────────────

MODE = os.getenv("MODE", "LOCAL").upper()
IS_LOCAL = MODE == "LOCAL"
IS_CLOUD = MODE == "CLOUD"

# ─────────────────────────────────────────────────────────────
# Core helper
# ─────────────────────────────────────────────────────────────

def get_env(name: str, default: Optional[str] = None) -> str:
    """
    Fetch environment variable or fail fast.

    Use ONLY for values that must exist at runtime.
    """
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


# ─────────────────────────────────────────────────────────────
# Runtime context
# ─────────────────────────────────────────────────────────────

AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
IS_LAMBDA = "AWS_LAMBDA_FUNCTION_NAME" in os.environ

# ─────────────────────────────────────────────────────────────
# Local filesystem paths (MODE=LOCAL)
# ─────────────────────────────────────────────────────────────

LOCAL_DATA_DIR = Path("data")
LOCAL_RAW_DIR = LOCAL_DATA_DIR / "raw"
LOCAL_CLEAN_DIR = LOCAL_DATA_DIR / "clean"

LOCAL_RAW_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_CLEAN_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Buckets (MODE=CLOUD)
# ─────────────────────────────────────────────────────────────

RAW_BUCKET = os.getenv("RAW_BUCKET")
CLEAN_BUCKET = os.getenv("CLEAN_BUCKET")

# Prefixes always normalized to end with "/"
RAW_PREFIX = (
    os.getenv("RAW_PREFIX", "public-health/raw")
    .strip("/") + "/"
)

CLEAN_PREFIX = (
    os.getenv("CLEAN_PREFIX", "public-health/clean")
    .strip("/") + "/"
)

# ─────────────────────────────────────────────────────────────
# Project structure
# ─────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(
    os.getenv("PROJECT_ROOT", Path.cwd())
).resolve()

# ─────────────────────────────────────────────────────────────
# Evidence paths (used by dashboard + analytics)
# ─────────────────────────────────────────────────────────────

EVIDENCE_DIR = Path(
    os.getenv("EVIDENCE_DIR", PROJECT_ROOT / "evidence")
)

ATHENA_EVIDENCE_DIR = EVIDENCE_DIR / "athena"
DASHBOARD_EVIDENCE_DIR = EVIDENCE_DIR / "dashboard"

ATHENA_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
DASHBOARD_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# ETL manifest
# ─────────────────────────────────────────────────────────────

ETL_MANIFEST_KEY = os.getenv(
    "ETL_MANIFEST_KEY",
    f"{CLEAN_PREFIX}manifest/etl_manifest.json",
)
