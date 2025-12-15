"""
src/etl/normalize_healthdata.py

Public Health ETL (Raw → Clean)

- MODE-aware: LOCAL (filesystem) / CLOUD (S3)
- Idempotent via manifest
- Partitioned Parquet output
- Lambda-compatible and local-runnable
"""

import json
import io
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Callable
from pathlib import Path

import boto3
import pandas as pd

from common.config import (
    MODE,
    RAW_BUCKET,
    CLEAN_BUCKET,
    RAW_PREFIX,
    CLEAN_PREFIX,
    ETL_MANIFEST_KEY,
    AWS_REGION,
    LOCAL_RAW_DIR,
    LOCAL_CLEAN_DIR,
)
from common.logging import setup_logging

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logger = setup_logging(__name__)
logger.info("ETL starting in MODE=%s", MODE)

# ------------------------------------------------------------------
# AWS client (CLOUD only)
# ------------------------------------------------------------------
s3 = boto3.client("s3", region_name=AWS_REGION)

# ------------------------------------------------------------------
# LOCAL paths
# ------------------------------------------------------------------
LOCAL_MANIFEST_PATH = Path("data/etl_manifest.json")

# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------
def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# ------------------------------------------------------------------
# Manifest handling
# ------------------------------------------------------------------
def load_manifest() -> Dict[str, Any]:
    if MODE == "LOCAL":
        if not LOCAL_MANIFEST_PATH.exists():
            return {"processed": {}}
        return json.loads(LOCAL_MANIFEST_PATH.read_text())

    try:
        obj = s3.get_object(Bucket=CLEAN_BUCKET, Key=ETL_MANIFEST_KEY)
        return json.loads(obj["Body"].read().decode("utf-8"))
    except s3.exceptions.NoSuchKey:
        return {"processed": {}}


def save_manifest(manifest: Dict[str, Any]) -> None:
    if MODE == "LOCAL":
        LOCAL_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOCAL_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
        return

    s3.put_object(
        Bucket=CLEAN_BUCKET,
        Key=ETL_MANIFEST_KEY,
        Body=json.dumps(manifest, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

# ------------------------------------------------------------------
# Parsers
# ------------------------------------------------------------------
def parse_gho_json(data: dict) -> pd.DataFrame:
    rows = data.get("value", [])
    records = []

    for rec in rows:
        try:
            year = int(rec["TimeDim"])
        except Exception:
            continue

        records.append({
            "country_code": rec.get("SpatialDim"),
            "year": year,
            "value": pd.to_numeric(rec.get("NumericValue"), errors="coerce"),
            "indicator_code": rec.get("IndicatorCode"),
        })

    df = pd.DataFrame(records)
    df = df[df["country_code"].str.len() == 3]
    df = df.dropna(subset=["country_code", "year"])
    df["year"] = df["year"].astype(int)

    return df


def parse_worldbank_json(data: list) -> pd.DataFrame:
    records = data[1] if isinstance(data, list) and len(data) >= 2 else data
    rows = []

    for rec in records:
        rows.append({
            "country_code": rec.get("countryiso3code"),
            "year": int(rec["date"]) if rec.get("date") else None,
            "value": pd.to_numeric(rec.get("value"), errors="coerce"),
            "indicator_id": rec.get("indicator", {}).get("id"),
        })

    df = pd.DataFrame(rows)
    df = df[df["country_code"].str.len() == 3]
    df = df.dropna(subset=["country_code", "year"])
    df["year"] = df["year"].astype(int)

    return df

# ------------------------------------------------------------------
# I/O helpers
# ------------------------------------------------------------------
def read_raw_bytes(raw_key: str) -> bytes:
    """
    raw_key:
      LOCAL → filename only (life_expectancy_2025....json)
      CLOUD → full S3 key (public-health/raw/...)
    """
    if MODE == "LOCAL":
        path = LOCAL_RAW_DIR / raw_key
        return path.read_bytes()

    obj = s3.get_object(Bucket=RAW_BUCKET, Key=raw_key)
    return obj["Body"].read()


def write_clean_parquet(
    endpoint: str,
    year: int,
    parquet_bytes: bytes,
) -> None:
    if MODE == "LOCAL":
        out_dir = LOCAL_CLEAN_DIR / endpoint / f"year={year}"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "data.parquet").write_bytes(parquet_bytes)
        return

    clean_key = f"{CLEAN_PREFIX}{endpoint}/year={year}/data.parquet"

    s3.put_object(
        Bucket=CLEAN_BUCKET,
        Key=clean_key,
        Body=parquet_bytes,
        ContentType="application/parquet",
    )

# ------------------------------------------------------------------
# Core transform
# ------------------------------------------------------------------
def transform_raw_object(
    raw_key: str,
    endpoint: str,
    parser: Callable[[Any], pd.DataFrame],
) -> bool:
    manifest = load_manifest()
    body = read_raw_bytes(raw_key)
    content_hash = sha256_bytes(body)

    if manifest["processed"].get(raw_key, {}).get("hash") == content_hash:
        logger.info("Skipped unchanged: %s", raw_key)
        return False

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        logger.error("Invalid JSON: %s", raw_key)
        return False

    df = parser(data)
    if df.empty:
        logger.warning("No valid rows parsed: %s", raw_key)
        manifest["processed"][raw_key] = {
            "hash": content_hash,
            "rows": 0,
            "processed_at": _utc_now(),
        }
        save_manifest(manifest)
        return False

    partitions = 0
    for year, group in df.groupby("year"):
        buf = io.BytesIO()
        group.to_parquet(buf, index=False)
        write_clean_parquet(endpoint, int(year), buf.getvalue())
        partitions += 1

    manifest["processed"][raw_key] = {
        "hash": content_hash,
        "rows": len(df),
        "written_partitions": partitions,
        "processed_at": _utc_now(),
    }
    save_manifest(manifest)

    logger.info(
        "Processed %s → %d partitions (%s)",
        raw_key,
        partitions,
        "LOCAL" if MODE == "LOCAL" else "S3",
    )
    return True

# ------------------------------------------------------------------
# Dataset routing
# ------------------------------------------------------------------
ROUTERS = {
    "life_expectancy": parse_gho_json,
    "malaria_incidence": parse_gho_json,
    "cholera": parse_gho_json,
    "wb_hospital_beds_per_1000": parse_worldbank_json,
    "wb_physicians_per_1000": parse_worldbank_json,
}

# ------------------------------------------------------------------
# Lambda entry point (CLOUD)
# ------------------------------------------------------------------
def lambda_handler(event, context):
    try:
        raw_key = event["Records"][0]["s3"]["object"]["key"]
    except Exception:
        return {"statusCode": 400, "body": "Invalid S3 event"}

    for name, parser in ROUTERS.items():
        if name in raw_key:
            transform_raw_object(raw_key, name, parser)
            break

    return {"statusCode": 200, "body": "ETL completed"}

# ------------------------------------------------------------------
# Local execution
# ------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Running ETL in LOCAL execution mode")

    for raw_file in LOCAL_RAW_DIR.glob("*.json"):
        for name, parser in ROUTERS.items():
            if name in raw_file.name:
                transform_raw_object(raw_file.name, name, parser)
                break

    logger.info("LOCAL ETL completed")
