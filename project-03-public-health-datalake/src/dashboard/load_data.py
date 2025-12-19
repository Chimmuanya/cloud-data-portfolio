"""
src/dashboard/load_data.py

Dataset loader & derivation layer for Project 3 dashboard.

Responsibilities:
- Load cleaned Parquet outputs
- Rehydrate partition columns
- Build defensible, chart-ready datasets
- MODE-aware (LOCAL filesystem / CLOUD S3)

This module is the ONLY place that knows where data lives.
"""
import io
from pathlib import Path
import pandas as pd
import boto3
from typing import Dict

# FIX 1: Import the pre-configured paths and context from common.config
from common.config import (
    MODE,
    CLEAN_BUCKET,
    CLEAN_PREFIX,
    LOCAL_CLEAN_DIR, # <-- Use the version that handles /tmp/
    IS_LAMBDA
)
from common.logging import setup_logging

logger = setup_logging(__name__)

# FIX 2: Remove the manual 'LOCAL_CLEAN = Path("data/clean")' definition.
# Use the imported LOCAL_CLEAN_DIR instead.

s3 = boto3.client("s3")

def _load_parquet(dataset: str) -> pd.DataFrame:
    """
    Load partitioned Parquet dataset and rehydrate 'year' column.
    """
    if MODE == "LOCAL":
        # FIX 3: Use the configuration-aware directory
        base = LOCAL_CLEAN_DIR / dataset
        paths = list(base.rglob("year=*/data.parquet"))

        if not paths:
            raise FileNotFoundError(
                f"No parquet files found for LOCAL dataset: {dataset} at {base}"
            )

        frames = []
        for p in paths:
            # Rehydrate partition column from folder name
            year = int(p.parent.name.split("=")[1])
            df = pd.read_parquet(p)
            df["year"] = year
            frames.append(df)

        return pd.concat(frames, ignore_index=True)

    # ---------------- CLOUD (S3) ----------------
    # This section is generally safe as it reads streams directly from S3
    prefix = f"{CLEAN_PREFIX}{dataset}/"
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=CLEAN_BUCKET, Prefix=prefix)

    frames = []
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".parquet"):
                continue

            # Extract year from key: .../year=YYYY/...
            try:
                year_part = [p for p in key.split("/") if p.startswith("year=")][0]
                year = int(year_part.split("=")[1])
            except (IndexError, ValueError):
                continue

            # Pandas can read the S3 body stream directly; no local file write needed.
            # FIX: Read the stream into a BytesIO buffer to allow seeking
            body = s3.get_object(Bucket=CLEAN_BUCKET, Key=key)["Body"].read()
            df = pd.read_parquet(io.BytesIO(body))

            df["year"] = year
            frames.append(df)

    if not frames:
        raise FileNotFoundError(
            f"No parquet files found for CLOUD dataset: {dataset} in bucket {CLEAN_BUCKET}"
        )

    return pd.concat(frames, ignore_index=True)


# ------------------------------------------------------------------
# DATASET BUILDERS (DEFENSIBLE ONLY)
# ------------------------------------------------------------------

def build_life_expectancy_global() -> pd.DataFrame:
    """
    Global life expectancy trend (mean across countries per year).
    """
    df = _load_parquet("life_expectancy")

    return (
        df.groupby("year", as_index=False)["value"]
        .mean()
        .sort_values("year")
    )


def build_malaria_top_countries() -> pd.DataFrame:
    """
    Top 5 malaria-burden countries (latest year),
    with full time series for heatmap + trend charts.
    """
    df = _load_parquet("malaria_incidence")

    latest_year = df["year"].max()

    top = (
        df[df["year"] == latest_year]
        .groupby("country_code")["value"]
        .mean()
        .nlargest(5)
        .index
    )

    return (
        df[df["country_code"].isin(top)]
        .sort_values(["country_code", "year"])
    )


def build_nigeria_physicians() -> pd.DataFrame:
    """
    Physician density trend for Nigeria only.
    """
    df = _load_parquet("wb_physicians_per_1000")

    return (
        df[df["country_code"] == "NGA"]
        .sort_values("year")
    )


def build_life_expectancy_ssa() -> pd.DataFrame:
    """
    Life expectancy for selected Sub-Saharan African countries.
    """
    df = _load_parquet("life_expectancy")

    ssa_codes = {
        "NGA", "GHA", "KEN", "ETH", "UGA", "TZA", "SEN"
    }

    return (
        df[df["country_code"].isin(ssa_codes)]
        .sort_values(["country_code", "year"])
    )


def build_life_expectancy_ssa_avg() -> pd.DataFrame:
    """
    SSA average life expectancy per year (REFERENCE LINE).
    """
    df = build_life_expectancy_ssa()

    return (
        df.groupby("year", as_index=False)["value"]
        .mean()
        .rename(columns={"value": "ssa_avg"})
        .sort_values("year")
    )


# ------------------------------------------------------------------
# PUBLIC API
# ------------------------------------------------------------------

def load_all() -> Dict[str, pd.DataFrame]:
    """
    Load and prepare all datasets required by registry.py.
    """
    logger.info("Loading dashboard datasets (MODE=%s)", MODE)

    return {
        # Chart 1
        "life_expectancy": build_life_expectancy_global(),

        # Charts 2 & 3
        "malaria_incidence_top_countries": build_malaria_top_countries(),

        # Chart 4
        "nigeria_physicians": build_nigeria_physicians(),

        # Chart 5 (explicit roles)
        "life_expectancy_ssa": build_life_expectancy_ssa(),
        "life_expectancy_ssa_avg": build_life_expectancy_ssa_avg(),
    }
