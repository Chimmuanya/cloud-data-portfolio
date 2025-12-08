"""
Canonical preprocessing utilities for Project 2 (E-commerce KPIs).

Usage examples (from project root):
python -m src.preprocess --raw ../data/raw/data.csv --out ../data/processed --steps all
Or run specific steps:
python -m src.preprocess --raw ../data/raw/data.csv --out ../data/processed --steps transform,daily,products,rfm

Outputs (by default written into --out directory):
sample_kpis.csv
daily_kpis.csv
top_products_summary.csv
rfm_customers.csv

Author: Generated/adapted from notebook flow
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# Logging: console + file (user preference 'modpptx.log')
LOG_FILENAME = "modpptx.log"
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILENAME, encoding="utf8"),
    ],
)


# ---------- I/O / defensive read ----------
def read_csv_defensive(
    path: Path, parse_dates: Optional[List[str]] = None, dayfirst: bool = False
) -> pd.DataFrame:
    """Safely reads a CSV file, attempts date parsing, and falls back if necessary."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Raw CSV not found: {path}")
    try:
        df = pd.read_csv(path, encoding="latin1", parse_dates=parse_dates or [], low_memory=False)
    except Exception as e:
        logger.warning("pd.read_csv(parse_dates) failed (%s). Retrying without parse_dates.", e)
        df = pd.read_csv(path, encoding="latin1", low_memory=False)
        # attempt manual parsing for common date column
        if parse_dates:
            for d in parse_dates:
                if d in df.columns:
                    df[d] = pd.to_datetime(df[d], dayfirst=dayfirst, errors="coerce")
    logger.info("Loaded raw file %s rows=%d cols=%d", path.name, len(df), len(df.columns))
    return df


# ---------- Canonical transform ----------
def canonical_transform(
    df: pd.DataFrame, invoice_date_col: str = "InvoiceDate", dayfirst: bool = False
) -> pd.DataFrame:
    """
    Parse dates, coerce numerics, detect cancellations, compute LineTotal, and flag negative revenue.
    Note: does not drop flagged rows — preserves auditability.
    """
    df = df.copy()

    # normalize column names
    df.columns = [c.strip() for c in df.columns]

    # parse invoice date safely: create parsed column first
    if invoice_date_col in df.columns:
        parsed = pd.to_datetime(df[invoice_date_col], dayfirst=dayfirst, errors="coerce")
        df["_invoice_date_orig"] = df[invoice_date_col]
        df["InvoiceDate_parsed"] = parsed

        # if parse failures are non-trivial, try month-first fallback
        n_fail = parsed.isna().sum()
        if n_fail > 0.05 * len(parsed):  # threshold: 5% failures -> try fallback
            parsed_mf = pd.to_datetime(df[invoice_date_col], dayfirst=False, errors="coerce")
            df["InvoiceDate_parsed_mf"] = parsed_mf
            if parsed_mf.isna().sum() < n_fail:
                logger.info("InvoiceDate: using month-first parsed datetimes (fewer NaT).")
                df["InvoiceDate"] = parsed_mf
            else:
                df["InvoiceDate"] = parsed
        else:
            df["InvoiceDate"] = parsed

        logger.info(
            "InvoiceDate parsed: failures=%d (%.2f%%)",
            df["InvoiceDate"].isna().sum(),
            100.0 * df["InvoiceDate"].isna().sum() / max(1, len(df)),
        )
    else:
        logger.warning("InvoiceDate column not found in raw data.")

    # coerce numeric columns
    for col in ["UnitPrice", "Price", "Quantity"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # detect cancellations via InvoiceNo starting with 'C' (common pattern)
    if "InvoiceNo" in df.columns:
        df["is_cancellation_candidate"] = df["InvoiceNo"].astype(str).str.upper().str.startswith("C", na=False)
    else:
        df["is_cancellation_candidate"] = False

    # compute LineTotal if not present
    if "LineTotal" not in df.columns:
        if {"UnitPrice", "Quantity"}.issubset(df.columns):
            df["LineTotal"] = df["UnitPrice"] * df["Quantity"]
        elif "Price" in df.columns:
            df["LineTotal"] = df["Price"]
        else:
            df["LineTotal"] = np.nan

    # negative revenue flag
    df["negative_revenue"] = df["LineTotal"] < 0

    # final canonical flags
    df["is_cancellation"] = df["is_cancellation_candidate"].fillna(False)  # allow override later

    # detect adjustment rows (financial adjustments / bad-debt write-offs)
    # heuristic from notebook: StockCode 'B' + Description contains 'ADJUST' / 'BAD DEBT'
    if "StockCode" in df.columns and "Description" in df.columns:
        df["is_adjustment"] = (
            df["StockCode"].astype(str).str.upper().eq("B")
            & df["Description"].astype(str).str.upper().str.contains("ADJUST|BAD DEBT|ADJUSTMENT", na=False)
        )
    else:
        df["is_adjustment"] = False

    # explicit operational flag used by KPIs: not cancellation, not adjustment, LineTotal present
    df["is_operational"] = (~df["is_cancellation"]) & (~df["is_adjustment"]) & df["LineTotal"].notna()

    logger.info(
        "Canonical transform complete. cancellations=%d adjustments=%d operational_rows=%d",
        int(df["is_cancellation"].sum()),
        int(df["is_adjustment"].sum()),
        int(df["is_operational"].sum()),
    )
    logger.debug("Columns now: %s", list(df.columns))
    return df


# ---------- Finalize cancellation/negatives ----------
def finalize_cancellations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure cancellations and negative-revenue logic is consistent.
    - If negatives appear only in invoices starting with 'C' we mark them as cancellation lines.
    - Heuristically mark certain negative non-cancellation rows as adjustments (e.g. StockCode 'B' adjustments).
    - Leaves odd negative rows flagged for manual inspection.
    """
    df = df.copy()

    # if LineTotal is missing, ensure numeric
    if "LineTotal" in df.columns:
        # find negatives not currently marked as cancellation
        neg_outside_mask = (df["LineTotal"] < 0) & (~df.get("is_cancellation", False))
        neg_outside = df[neg_outside_mask]

        logger.info("Negative LineTotal rows outside cancellation invoices: %d", len(neg_outside))

        # If these match the adjustment heuristic (StockCode == 'B' or Description contains ADJUST),
        # mark them as is_adjustment to exclude from operational KPIs.
        if len(neg_outside) > 0 and {"StockCode", "Description"}.issubset(df.columns):
            mask_adj = (
                df["StockCode"].astype(str).str.upper().eq("B")
                & df["Description"].astype(str).str.upper().str.contains("ADJUST|BAD DEBT|ADJUSTMENT", na=False)
                & (df["LineTotal"] < 0)
            )
            if mask_adj.any():
                df.loc[mask_adj, "is_adjustment"] = True
                logger.info("Marked %d negative non-cancellation rows as is_adjustment.", int(mask_adj.sum()))

    else:
        logger.warning("LineTotal missing when finalizing cancellations.")

    # ensure is_operational exists and is consistent
    df["is_operational"] = (
        (~df.get("is_cancellation", False))
        & (~df.get("is_adjustment", False))
        & df.get("LineTotal").notna()
    )

    # final sanity logging
    neg_non_cancel_remaining = int(((df["LineTotal"] < 0) & (~df["is_cancellation"])).sum())
    logger.info(
        "Finalize cancellations: cancellations=%d adjustments=%d negative_non_cancel_remaining=%d",
        int(df.get("is_cancellation", False).sum()) if "is_cancellation" in df.columns else 0,
        int(df.get("is_adjustment", False).sum()) if "is_adjustment" in df.columns else 0,
        neg_non_cancel_remaining,
    )
    return df


# ---------- KPI computations ----------
def compute_daily_kpis(df: pd.DataFrame, require_operational: bool = True) -> pd.DataFrame:
    """
    Returns a daily (date) DataFrame with:
    - date
    - tx_all (all lines)
    - transactions (unique InvoiceNo for operational rows)
    - operational_revenue (sum LineTotal excluding cancellations & adjustments)
    - cancellations (count)
    - aov (avg order value computed at invoice-level)
    """
    df = df.copy()

    # ensure InvoiceDate is datetime
    if "InvoiceDate" not in df.columns or not pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]):
        raise RuntimeError(
            "InvoiceDate missing or not datetime. Run canonical_transform and ensure InvoiceDate parsed."
        )
    df["date"] = df["InvoiceDate"].dt.floor("d")

    # operational rows = prefer explicit flag if present
    if "is_operational" in df.columns:
        df["operational"] = df["is_operational"]
    else:
        df["operational"] = (~df["is_cancellation"]) & (df["LineTotal"].notna())

    # tx_all: number of lines per day
    daily_all = df.groupby("date").size().rename("tx_all")

    # operational transactions: unique invoice count per day (operational)
    if "InvoiceNo" in df.columns:
        daily_ops_tx = df[df["operational"]].groupby("date")["InvoiceNo"].nunique().rename("transactions")
    else:
        daily_ops_tx = df[df["operational"]].groupby("date").size().rename("transactions")

    # operational revenue
    daily_rev = df[df["operational"]].groupby("date")["LineTotal"].sum().rename("operational_revenue")

    # cancellations count (invoices flagged)
    daily_canc = df[df.get("is_cancellation", False)].groupby("date").size().rename("cancellations")

    # combine
    daily = pd.concat([daily_all, daily_ops_tx, daily_rev, daily_canc], axis=1).fillna(0)
    daily = daily.reset_index().sort_values("date")

    # compute AOV (average order value) at invoice-level:
    if "InvoiceNo" in df.columns:
        inv_rev = (
            df[df["operational"]].groupby(["date", "InvoiceNo"])["LineTotal"].sum().rename("invoice_revenue")
        )
        aov = inv_rev.groupby("date").mean().rename("aov")
        daily = daily.set_index("date").join(aov).reset_index()
        daily["aov"] = daily["aov"].fillna(0.0)
    else:
        daily["aov"] = 0.0

    # ensure numeric types
    for c in ["tx_all", "transactions", "operational_revenue", "cancellations"]:
        if c in daily.columns:
            daily[c] = pd.to_numeric(daily[c], errors="coerce").fillna(0)

    return daily


# ---------- Top products summary ----------
def top_products_summary(
    df: pd.DataFrame, product_key_candidates: Optional[List[str]] = None, top_n: int = 10
) -> pd.DataFrame:
    """
    Aggregate revenue and volume by an identified product key (StockCode etc).
    Returns the full aggregated DataFrame (unsliced) with rev_share and qty_share.
    """
    df = df.copy()

    product_key_candidates = product_key_candidates or [
        "StockCode",
        "ProductID",
        "ItemID",
        "SKU",
        "Product",
    ]
    prod_key = next((c for c in product_key_candidates if c in df.columns), None)

    if prod_key is None:
        raise RuntimeError(
            "No product identifier column found. Add one of: %s" % product_key_candidates
        )
    # operational only
    oper = df[
        ~df.get("is_cancellation", False)
        & df.get("LineTotal").notna()
        & ~df.get("is_adjustment", False)
    ].copy()

    # ensure quantity exists
    if "Quantity" not in oper.columns:
        oper["Quantity"] = 0

    agg = oper.groupby(prod_key).agg(
        revenue=("LineTotal", "sum"),
        qty=("Quantity", "sum"),
        tx_lines=("InvoiceNo", "count"),
        distinct_customers=(
            "CustomerID",
            lambda s: s.nunique() if "CustomerID" in oper.columns else 0,
        ),
    ).reset_index()

    # attach description first non-null if present
    if "Description" in oper.columns:
        desc = oper.groupby(prod_key)["Description"].agg(
            lambda s: next((x for x in s.dropna().astype(str)), "")
        )
        desc = desc.reset_index().rename(columns={"Description": "description"})
        agg = agg.merge(desc, on=prod_key, how="left")
    else:
        agg["description"] = ""

    # create short description for display (useful for dashboard)
    agg["desc_short"] = agg["description"].fillna("").apply(lambda s: (s[:57] + "...") if len(s) > 60 else s)

    # compute avg_price defensively
    # avoid division by zero: if qty == 0 set avg_price to NaN
    agg["avg_price"] = (agg["revenue"] / agg["qty"]).replace([np.inf, -np.inf], np.nan)
    agg.loc[agg["qty"] == 0, "avg_price"] = np.nan

    # compute rev/qty share (make sure denominator not zero)
    total_rev = agg["revenue"].sum() if agg["revenue"].sum() != 0 else 1.0
    total_qty = agg["qty"].sum() if agg["qty"].sum() != 0 else 1.0
    agg["rev_share"] = agg["revenue"] / total_rev
    agg["qty_share"] = agg["qty"] / total_qty

    # is_meta heuristic (short code all-alpha or very short)
    agg["is_meta"] = agg[prod_key].astype(str).str.len().le(3) | agg[prod_key].astype(str).str.match(
        r"^[A-Z]+$"
    )

    total_rev = agg["revenue"].sum()
    total_qty = agg["qty"].sum() if agg["qty"].sum() != 0 else 1.0
    agg["rev_share"] = agg["revenue"] / (total_rev or 1.0)
    agg["qty_share"] = agg["qty"] / total_qty

    # sorting
    agg = agg.sort_values("revenue", ascending=False).reset_index(drop=True)
    return agg


# ---------- Simple RFM ----------
def compute_rfm(df: pd.DataFrame, snapshot_date: Optional[datetime] = None) -> pd.DataFrame:
    """
    Compute a simple RFM table for customers.
    Returns: DataFrame with recency_days, frequency, monetary, R_rank, F_rank, M_rank, RFM_score
    """
    if "CustomerID" not in df.columns:
        raise RuntimeError("CustomerID column not present; cannot compute RFM")
    oper = df[~df.get("is_cancellation", False) & ~df.get("is_adjustment", False)].copy()
    snapshot_date = snapshot_date or (oper["InvoiceDate"].max() + timedelta(days=1))

    # group by customer
    agg = oper.groupby("CustomerID").agg(
        last_tx=("InvoiceDate", "max"),
        recency_days=("InvoiceDate", lambda x: (snapshot_date - x.max()).days),
        frequency=(
            "InvoiceNo",
            lambda s: s.nunique() if "InvoiceNo" in oper.columns else s.count(),
        ),
        monetary=("LineTotal", "sum"),
    ).reset_index()

    # defensive: handle missing / NaN recency (customers with no date)
    agg["recency_days"] = pd.to_numeric(agg["recency_days"], errors="coerce").fillna(np.inf)
    agg["frequency"] = pd.to_numeric(agg["frequency"], errors="coerce").fillna(0).astype(int)
    agg["monetary"] = pd.to_numeric(agg["monetary"], errors="coerce").fillna(0.0)

    # ranks: recency inverted (lower recency => better)
    try:
        agg["R_rank"] = pd.qcut(agg["recency_days"].rank(method="first"), 4, labels=[4, 3, 2, 1])
        agg["F_rank"] = pd.qcut(agg["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4])
        agg["M_rank"] = pd.qcut(agg["monetary"].rank(method="first"), 4, labels=[1, 2, 3, 4])
    except ValueError as e:
        # fallback: when there are fewer unique values than bins
        logger.warning("pd.qcut failed (%s). Falling back to rank percentiles.", e)
        agg["R_rank"] = pd.cut(agg["recency_days"], bins=4, labels=[4, 3, 2, 1]).astype(object)
        agg["F_rank"] = pd.cut(
            agg["frequency"].rank(method="first"), bins=4, labels=[1, 2, 3, 4]
        ).astype(object)
        agg["M_rank"] = pd.cut(
            agg["monetary"].rank(method="first"), bins=4, labels=[1, 2, 3, 4]
        ).astype(object)

    # convert ranks to int where possible (coerce NaNs)
    for col in ("R_rank", "F_rank", "M_rank"):
        agg[col] = pd.to_numeric(agg[col], errors="coerce").fillna(0).astype(int)

    agg["RFM_score"] = agg["R_rank"] * 100 + agg["F_rank"] * 10 + agg["M_rank"]
    return agg


# ---------- Export helper ----------
def save_df(df: pd.DataFrame, path: Path, index: bool = False) -> Path:
    """Saves a DataFrame to a specified path and logs the action."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index)
    logger.info("Saved %s (rows=%d) to %s", path.name, len(df), path)
    return path


# ---------- CLI / driver ----------
def run_pipeline(raw: Path, out_dir: Path, steps: List[str]) -> Dict[str, Path]:
    """Runs the full ETL pipeline based on specified steps."""
    out_dir = Path(out_dir)
    raw = Path(raw)
    steps = [s.strip().lower() for s in steps]
    results = {}

    # ensure output directory exists
    out_dir.mkdir(parents=True, exist_ok=True)

    df_raw = read_csv_defensive(raw, parse_dates=["InvoiceDate"], dayfirst=False)

    # --- Transform Step ---
    if "transform" in steps or "all" in steps:
        df = canonical_transform(df_raw, invoice_date_col="InvoiceDate", dayfirst=False)
        df = finalize_cancellations(df)

        # save sample for manual review (top 500 most recent operational)
        sample_cols = [
            "InvoiceDate",
            "InvoiceNo",
            "CustomerID",
            "StockCode",
            "Description",
            "Quantity",
            "UnitPrice",
            "LineTotal",
            "is_cancellation",
            "is_adjustment",
            "is_operational",
        ]
        existing_cols = [c for c in sample_cols if c in df.columns]
        sample = (
            df.loc[df["LineTotal"].notna(), existing_cols]
            .sort_values("InvoiceDate", ascending=False)
            .head(500)
        )
        sample_path = save_df(sample, out_dir / "sample_kpis.csv", index=False)
        results["sample_kpis"] = sample_path
    else:
        # if transform step not requested we still need df for other steps
        df = canonical_transform(df_raw, invoice_date_col="InvoiceDate", dayfirst=False)
        df = finalize_cancellations(df)

    # --- Daily KPIs ---
    if "daily" in steps or "all" in steps:
        daily = compute_daily_kpis(df)
        daily_path = save_df(daily, out_dir / "daily_kpis.csv", index=False)
        results["daily_kpis"] = daily_path

    # --- Top Products ---
    if "products" in steps or "all" in steps:
        prod = top_products_summary(df)
        prod_path = save_df(prod, out_dir / "top_products_summary.csv", index=False)
        results["top_products"] = prod_path

    # --- RFM ---
    if "rfm" in steps or "all" in steps:
        if "CustomerID" in df.columns:
            rfm = compute_rfm(df)
            rfm_path = save_df(rfm, out_dir / "rfm_customers.csv", index=False)
            results["rfm"] = rfm_path
        else:
            logger.warning("CustomerID missing: skipping RFM step.")

    # --- Additional artifact outputs (parquet + metadata) ---
    # Write parquet versions and metadata.json similar to notebook flow
    try:
        # write parquet outputs if corresponding variables exist
        if "daily" in locals():
            try:
                daily.to_parquet(out_dir / "daily_kpis.parquet", index=False)
                logger.info("Wrote parquet: daily_kpis.parquet")
            except Exception as e:
                logger.warning("Failed to write daily parquet (%s).", e)
        if "prod" in locals():
            try:
                prod.to_parquet(out_dir / "top_products_summary.parquet", index=False)
                logger.info("Wrote parquet: top_products_summary.parquet")
            except Exception as e:
                logger.warning("Failed to write products parquet (%s).", e)
        if "rfm" in locals():
            try:
                rfm.to_parquet(out_dir / "rfm_customers.parquet", index=False)
                logger.info("Wrote parquet: rfm_customers.parquet")
            except Exception as e:
                logger.warning("Failed to write rfm parquet (%s).", e)

        # write metadata.json
        meta = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "rows": {
                "daily": len(daily) if "daily" in locals() else 0,
                "products": len(prod) if "prod" in locals() else 0,
                "rfm": len(rfm) if "rfm" in locals() else 0,
            },
            "source": str(raw),
        }
        with open(out_dir / "metadata.json", "w") as fh:
            json.dump(meta, fh, indent=2)
        logger.info("Wrote metadata.json to %s", out_dir / "metadata.json")
    except Exception as e:
        logger.warning("Failed to write supplemental artifacts (parquet/metadata): %s", e)

    return results


def _parse_args():
    """Parses command line arguments."""
    p = argparse.ArgumentParser(description="Project 2 preprocessing/ETL utilities")
    p.add_argument(
        "--raw", required=True, help="Path to raw CSV (e.g. ../data/raw/data.csv)"
    )
    p.add_argument(
        "--out",
        required=True,
        help="Output directory to write processed CSVs (e.g. ../data/processed)",
    )
    p.add_argument(
        "--steps",
        default="all",
        help="Comma-separated steps: transform,daily,products,rfm or 'all'",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    raw_path = Path(args.raw)
    out_path = Path(args.out)
    steps = args.steps.split(",") if args.steps else ["all"]

    logger.info("Starting preprocess pipeline. raw=%s out=%s steps=%s", raw_path, out_path, steps)
    results = run_pipeline(raw_path, out_path, steps)
    logger.info("Pipeline finished. Produced: %s", results)
