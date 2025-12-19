"""
src/ingest/app.py
Public Health Raw Ingest

- AWS Lambda compatible
- Local-first execution
- Robust HTTP retries with backoff
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import boto3

from common.config import (
    RAW_BUCKET,
    RAW_PREFIX,
    AWS_REGION,
    MODE,
    LOCAL_RAW_DIR,
)
from common.logging import setup_logging

# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────
logger = setup_logging(__name__)
logger.info("Ingest starting in MODE=%s", MODE)

# ─────────────────────────────────────────────────────────────
# AWS client (used only in CLOUD mode)
# ─────────────────────────────────────────────────────────────
s3 = boto3.client("s3", region_name=AWS_REGION)

# ─────────────────────────────────────────────────────────────
# HTTP session with retries + backoff
# ─────────────────────────────────────────────────────────────

def build_http_session() -> requests.Session:
    """
    Shared HTTP session with bounded retries and exponential backoff.
    Safe for Lambda and local execution.
    """
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


HTTP = build_http_session()

# ─────────────────────────────────────────────────────────────
# Endpoints (authoritative list)
# ─────────────────────────────────────────────────────────────

ENDPOINTS: List[Dict[str, str]] = [
    {
        "name": "life_expectancy",
        "url": "https://ghoapi.azureedge.net/api/WHOSIS_000001?$filter=(TimeDim ge 2000)",
    },
    {
        "name": "malaria_incidence",
        "url": "https://ghoapi.azureedge.net/api/MALARIA_EST_INCIDENCE?$filter=(TimeDim ge 2020)",
    },
    {
        "name": "cholera",
        "url": "https://ghoapi.azureedge.net/api/CHOLERA_0000000001?$filter=(TimeDim ge 2000)",
    },
    {
        "name": "who_outbreaks",
        "url": "api/emergencies/diseaseoutbreaknews",
    },
    {
        "name": "wb_hospital_beds_per_1000",
        "url": (
            "https://api.worldbank.org/v2/country/all/"
            "indicator/SH.MED.BEDS.ZS"
            "?format=json&date=2000:2024&per_page=20000"
        ),
    },
    {
        "name": "wb_physicians_per_1000",
        "url": (
            "https://api.worldbank.org/v2/country/all/"
            "indicator/SH.MED.PHYS.ZS"
            "?format=json&date=2000:2024&per_page=20000"
        ),
    },
]

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _detect_extension(content_type: str | None) -> str:
    if content_type and "csv" in content_type.lower():
        return "csv"
    return "json"


# ─────────────────────────────────────────────────────────────
# Core ingest logic
# ─────────────────────────────────────────────────────────────

def fetch_and_store(endpoint: Dict[str, str]) -> Dict[str, Any]:
    """
    Fetch endpoint and store raw payload.

    CLOUD:
      s3://<RAW_BUCKET>/<RAW_PREFIX>/<dataset>/<timestamp>-<uuid>.{json|csv}

    LOCAL:
      <LOCAL_RAW_DIR>/<dataset>_<timestamp>-<uuid>.{json|csv}
    """
    name = endpoint["name"]
    url = endpoint["url"]

    logger.info("Fetching dataset=%s", name)
    resp = HTTP.get(url, timeout=(5, 60), stream=True)

    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status_code} for {name}")

    # For smaller files, reading into memory is fine.
    # For a portfolio project, this is acceptable.
    content = resp.content

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ext = _detect_extension(resp.headers.get("Content-Type"))
    filename = f"{ts}-{uuid.uuid4().hex}.{ext}"

    # ─────────────── LOCAL MODE (Fedora/Dev) ───────────────
    # Only run this if we are intentionally in LOCAL mode.
    if MODE == "LOCAL":
        # Safe because config.py redirects this to /tmp if IS_LAMBDA is True
        LOCAL_RAW_DIR.mkdir(parents=True, exist_ok=True)
        local_path = LOCAL_RAW_DIR / f"{name}_{filename}"
        local_path.write_bytes(content)

        return {
            "dataset": name,
            "storage": "LOCAL",
            "path": str(local_path)
        }

    # ─────────────── CLOUD MODE (AWS Lambda) ───────────────
    key = f"{RAW_PREFIX}{name}/{filename}"

    s3.put_object(
        Bucket=RAW_BUCKET,
        Key=key,
        Body=content, # Uploading bytes directly to S3
        ContentType=resp.headers.get("Content-Type", "application/json"),
    )


    logger.info(
        "Stored dataset=%s bytes=%s s3_key=%s",
        name,
        f"{len(content):,}",
        key,
        )

    return {
        "dataset": name,
        "storage": "S3",
        "key": key
    }

# ─────────────────────────────────────────────────────────────
# Lambda handler
# ─────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    results: List[Dict[str, Any]] = []

    for ep in ENDPOINTS:
        try:
            results.append(fetch_and_store(ep))
        except Exception as exc:
            logger.exception("FAILED ingest dataset=%s", ep["name"])
            results.append({
                "dataset": ep["name"],
                "error": str(exc),
            })

    return {
        "statusCode": 200,
        "body": json.dumps({
            "status": "ok",
            "datasets_attempted": len(ENDPOINTS),
            "results": results,
        }),
    }


# ─────────────────────────────────────────────────────────────
# Local execution
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("Running ingest in LOCAL execution mode")
    output = lambda_handler({}, None)
    print(json.dumps(json.loads(output["body"]), indent=2))
