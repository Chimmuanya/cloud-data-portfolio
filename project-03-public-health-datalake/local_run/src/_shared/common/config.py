"""
src/common/config.py
Central configuration for Project 3.

PROJECT_ROOT = project-03-public-health-datalake
LOCAL_RUN is a sandboxed local simulation environment.
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
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
IS_LAMBDA = "AWS_LAMBDA_FUNCTION_NAME" in os.environ


def get_env(name: str, default: Optional[str] = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


# ─────────────────────────────────────────────────────────────
# 2. Cloud Configuration (Buckets & Prefixes)
# ─────────────────────────────────────────────────────────────
if IS_CLOUD or IS_LAMBDA:
    RAW_BUCKET = get_env("RAW_BUCKET").lower()
    CLEAN_BUCKET = get_env("CLEAN_BUCKET").lower()
    EVIDENCE_BUCKET = get_env("EVIDENCE_BUCKET").lower()
else:
    RAW_BUCKET = os.getenv("RAW_BUCKET", "").lower()
    CLEAN_BUCKET = os.getenv("CLEAN_BUCKET", "").lower()
    EVIDENCE_BUCKET = os.getenv("EVIDENCE_BUCKET", "").lower()

ATHENA_DATABASE = "project03_db"
ATHENA_OUTPUT_PREFIX = "athena-results"

ATHENA_OUTPUT_PATH = (
    f"s3://{EVIDENCE_BUCKET}/{ATHENA_OUTPUT_PREFIX}/"
    if EVIDENCE_BUCKET else ""
)

RAW_PREFIX = os.getenv("RAW_PREFIX", "public-health/raw").strip("/") + "/"
CLEAN_PREFIX = os.getenv("CLEAN_PREFIX", "public-health/clean").strip("/") + "/"

ETL_MANIFEST_KEY = os.getenv(
    "ETL_MANIFEST_KEY",
    f"{CLEAN_PREFIX}manifest/etl_manifest.json",
)

# ─────────────────────────────────────────────────────────────
# 3. Filesystem Paths (AUTHORITATIVE)
# ─────────────────────────────────────────────────────────────
if IS_LAMBDA:
    BASE_DATA_PATH = Path("/tmp") / "data"
    BASE_EVIDENCE_PATH = Path("/tmp") / "evidence"

else:
    def find_project_root(start: Path) -> Path:
        """
        PROJECT_ROOT is the directory that contains `local_run/`
        """
        for p in [start, *start.parents]:
            if (p / "local_run").is_dir():
                return p
        raise RuntimeError(
            "PROJECT_ROOT could not be determined (missing local_run/)"
        )

    PROJECT_ROOT = find_project_root(Path(__file__).resolve())

    LOCAL_RUN_ROOT = PROJECT_ROOT / "local_run"
    BASE_DATA_PATH = LOCAL_RUN_ROOT / "local_data"
    BASE_EVIDENCE_PATH = LOCAL_RUN_ROOT / "evidence"


# ─────────────────────────────────────────────────────────────
# 4. Local filesystem paths
# ─────────────────────────────────────────────────────────────
LOCAL_DATA_DIR = BASE_DATA_PATH
LOCAL_RAW_DIR = BASE_DATA_PATH / "raw"
LOCAL_CLEAN_DIR = BASE_DATA_PATH / "clean"

ATHENA_EVIDENCE_DIR = BASE_EVIDENCE_PATH / "athena"
DASHBOARD_EVIDENCE_DIR = BASE_EVIDENCE_PATH / "dashboard"


# ─────────────────────────────────────────────────────────────
# 5. Ensure directories exist (LOCAL only)
# ─────────────────────────────────────────────────────────────
if IS_LOCAL:
    for d in (
        LOCAL_RAW_DIR,
        LOCAL_CLEAN_DIR,
        ATHENA_EVIDENCE_DIR,
        DASHBOARD_EVIDENCE_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)
