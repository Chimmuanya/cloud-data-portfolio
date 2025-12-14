import json
import io
import boto3
import pandas as pd
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any

from common.config import (
    RAW_BUCKET,
    CLEAN_BUCKET,
    RAW_PREFIX,
    CLEAN_PREFIX,
    ETL_MANIFEST_KEY,
    AWS_REGION,
)
from common.logging import setup_logging

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logger = setup_logging(__name__)

# ------------------------------------------------------------------
# AWS client
# ------------------------------------------------------------------
s3 = boto3.client("s3", region_name=AWS_REGION)

# ------------------------------------------------------------------
# Manifest handling (S3-based, idempotent)
# ------------------------------------------------------------------
def load_manifest() -> Dict[str, Any]:
    try:
        obj = s3.get_object(Bucket=CLEAN_BUCKET, Key=ETL_MANIFEST_KEY)
        return json.loads(obj["Body"].read().decode("utf-8"))
    except s3.exceptions.NoSuchKey:
        return {"processed": {}}


def save_manifest(manifest_data: Dict[str, Any]) -> None:
    s3.put_object(
        Bucket=CLEAN_BUCKET,
        Key=ETL_MANIFEST_KEY,
        Body=json.dumps(manifest_data, indent=2).encode("utf-8"),
        ContentType="application/json",
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# ------------------------------------------------------------------
# WHO GHO Parser
# ------------------------------------------------------------------
def parse_gho_json(data: dict) -> pd.DataFrame:
    rows = data.get("value", [])
    if not rows:
        return pd.DataFrame()

    records = []
    for rec in rows:
        try:
            year = int(rec["TimeDim"]) if rec.get("TimeDim") else None
        except (ValueError, TypeError):
            year = None

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

    return df[["country_code", "year", "value", "indicator_code"]]

# ------------------------------------------------------------------
# World Bank Parser
# ------------------------------------------------------------------
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

    return df[["country_code", "year", "value", "indicator_id"]]

# ------------------------------------------------------------------
# Core transform
# ------------------------------------------------------------------
def transform_raw_object(raw_key: str, endpoint_name: str, parser) -> bool:
    manifest = load_manifest()

    obj = s3.get_object(Bucket=RAW_BUCKET, Key=raw_key)
    body_bytes = obj["Body"].read()
    current_hash = sha256_bytes(body_bytes)

    if manifest["processed"].get(raw_key, {}).get("hash") == current_hash:
        logger.info("Skipped unchanged: %s", raw_key)
        return False

    try:
        data = json.loads(body_bytes)
    except json.JSONDecodeError as exc:
        logger.error("JSON decode error on %s: %s", raw_key, exc)
        return False

    df = parser(data)
    if df.empty:
        logger.warning("No valid rows parsed from %s", raw_key)
        manifest["processed"][raw_key] = {
            "hash": current_hash,
            "rows": 0,
            "processed_at": _utc_now(),
        }
        save_manifest(manifest)
        return False

    written = 0
    for year, group in df.groupby("year"):
        buf = io.BytesIO()
        group.to_parquet(buf, index=False)

        clean_key = (
            f"{CLEAN_PREFIX}"
            f"{endpoint_name}/"
            f"year={int(year)}/data.parquet"
        )

        s3.put_object(
            Bucket=CLEAN_BUCKET,
            Key=clean_key,
            Body=buf.getvalue(),
            ContentType="application/parquet",
        )
        written += 1

    manifest["processed"][raw_key] = {
        "hash": current_hash,
        "rows": len(df),
        "written_partitions": written,
        "processed_at": _utc_now(),
    }
    save_manifest(manifest)

    logger.info(
        "Processed %s → %d partitions → s3://%s/%s",
        raw_key, written, CLEAN_BUCKET, clean_key
    )
    return True


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"

# ------------------------------------------------------------------
# Lambda entry point
# ------------------------------------------------------------------
def lambda_handler(event, context):
    try:
        record = event["Records"][0]["s3"]
        raw_key = record["object"]["key"]
        logger.info("Processing raw object: %s", raw_key)
    except (KeyError, IndexError):
        return {"statusCode": 400, "body": "Invalid S3 event"}

    if "life_expectancy" in raw_key:
        parser = parse_gho_json
        endpoint = "life_expectancy"
    elif "malaria_incidence" in raw_key:
        parser = parse_gho_json
        endpoint = "malaria_incidence"
    elif "cholera" in raw_key:
        parser = parse_gho_json
        endpoint = "cholera"
    elif "wb_hospital_beds_per_1000" in raw_key:
        parser = parse_worldbank_json
        endpoint = "wb_hospital_beds_per_1000"
    elif "wb_physicians_per_1000" in raw_key:
        parser = parse_worldbank_json
        endpoint = "wb_physicians_per_1000"
    else:
        logger.info("Ignored (no parser): %s", raw_key)
        return {"statusCode": 200, "body": f"Ignored: {raw_key}"}

    success = transform_raw_object(raw_key, endpoint, parser)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "raw_key": raw_key,
            "endpoint": endpoint,
            "success": success,
        }),
    }
