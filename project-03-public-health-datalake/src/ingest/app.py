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

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import boto3

from common.config import (
    RAW_BUCKET,
    RAW_PREFIX,
    CLEAN_BUCKET,
    AWS_REGION,
)
from common.logging import setup_logging

# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────
logger = setup_logging(__name__)

# ─────────────────────────────────────────────────────────────
# AWS client
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
        "url": "https://www.who.int/api/news/diseaseoutbreaknews",
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

def fetch_and_store_to_s3(endpoint: Dict[str, str]) -> Dict[str, Any]:
    """
    Fetch endpoint and write raw payload to S3:
    s3://<RAW_BUCKET>/<RAW_PREFIX>/<dataset>/<timestamp>-<uuid>.{json|csv}
    """
    name = endpoint["name"]
    url = endpoint["url"]

    logger.info("Fetching dataset=%s", name)

    resp = HTTP.get(url, timeout=60)

    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status_code} for {name} after retries")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ext = _detect_extension(resp.headers.get("Content-Type"))
    filename = f"{ts}-{uuid.uuid4().hex}.{ext}"
    key = f"{RAW_PREFIX}{name}/{filename}"

    s3.put_object(
        Bucket=RAW_BUCKET,
        Key=key,
        Body=resp.content,
        ContentType=resp.headers.get("Content-Type", "application/json"),
    )

    logger.info(
        "Stored dataset=%s bytes=%s s3_key=%s",
        name,
        f"{len(resp.content):,}",
        key,
    )

    return {
        "dataset": name,
        "s3_key": key,
        "bytes": len(resp.content),
    }


# ─────────────────────────────────────────────────────────────
# Lambda handler
# ─────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    results: List[Dict[str, Any]] = []

    for ep in ENDPOINTS:
        try:
            results.append(fetch_and_store_to_s3(ep))
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
# Local execution (Step 2)
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("Running ingest in LOCAL mode")
    out = lambda_handler({}, None)
    print(json.dumps(json.loads(out["body"]), indent=2))
