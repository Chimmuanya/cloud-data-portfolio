"""
app.py — Streamlit dashboard for Project 2 (E-commerce KPI Dashboard)

Features:
 - Loads processed outputs (parquet/csv) from S3 or local disk
 - Overview: total revenue, transactions, AOV, trend charts
 - Products: top by revenue / quantity, rev-share pareto
 - Customers: RFM segmentation summary and top customers
 - Data quality panel: days with zero ops / sample bad rows
 - Download buttons for CSV exports

How to run (local dev):
  1. pip install -r requirements.txt
     (requirements should include: streamlit pandas pyarrow s3fs boto3 plotly)
  2. export AWS credentials or use EC2 role with s3:GetObject
  3. streamlit run app.py

Config:
 - Set BUCKET and PREFIX at top of file OR export environment variables:
     export KPI_BUCKET="your-bucket"
     export KPI_PREFIX="project-02/processed/"
 - Local fallback: ./data/processed/daily_kpis.parquet etc.

Security:
 - When running on EC2, attach an IAM role with s3:GetObject & s3:ListBucket for the bucket/prefix.
 - For GitHub Actions / CI, use a limited S3 PutObject user (not required for the app).

Author: adapted from notebook flow for Project 2
"""

from pathlib import Path
import os
import io
import json
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# Optional S3 filesystem
try:
    import s3fs
    S3FS_AVAILABLE = True
except Exception:
    S3FS_AVAILABLE = False

# ---------- Config ----------
BUCKET = os.environ.get("KPI_BUCKET", "")       # e.g. "your-bucket"
PREFIX = os.environ.get("KPI_PREFIX", "project-02/processed/")  # prefix inside the bucket

# Get the present working directory
current_directory = os.getcwd()
LOCAL_OUT_DIR = Path(os.environ.get("LOCAL_OUT_DIR", current_directory + "/data/processed"))

# Filenames we expect (written by preprocess.py)
FILES = {
    "daily": "daily_kpis.parquet",
    "products": "top_products_summary.parquet",
    "rfm": "rfm_customers.parquet",
    "sample": "sample_kpis.csv",
    "metadata": "metadata.json",
}

# ---------- Helpers: load data ----------
def s3_path(key: str) -> str:
    return f"s3://{BUCKET}/{PREFIX}{key}" if BUCKET else ""

@st.cache_data(ttl=600)
def load_parquet_from_s3_or_local(key: str) -> pd.DataFrame:
    """
    Try S3 first (if configured), otherwise fall back to LOCAL_OUT_DIR.
    Returns DataFrame (empty DataFrame if file not found).
    """
    fname = FILES.get(key, key)
    # Try S3
    if BUCKET and S3FS_AVAILABLE:
        path = s3_path(fname)
        try:
            fs = s3fs.S3FileSystem()
            with fs.open(path, "rb") as f:
                df = pd.read_parquet(f)
            return df
        except Exception as e:
            st.debug(f"Could not read {path} from S3: {e}")
    # Local fallback
    local_path = LOCAL_OUT_DIR / fname
    if local_path.exists():
        try:
            if local_path.suffix in [".parquet", ".pq"]:
                return pd.read_parquet(local_path)
            else:
                return pd.read_csv(local_path, parse_dates=True)
        except Exception as e:
            st.error(f"Failed to load local file {local_path}: {e}")
            return pd.DataFrame()
    else:
        st.warning(f"No file found for {fname} in S3 or local ({local_path}).")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_json_from_s3_or_local(key: str) -> dict:
    fname = FILES.get(key, key)
    if BUCKET and S3FS_AVAILABLE:
        path = s3_path(fname)
        try:
            fs = s3fs.S3FileSystem()
            with fs.open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    local_path = LOCAL_OUT_DIR / fname
    if local_path.exists():
        try:
            with open(local_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

# ---------- Small util functions ----------
def ensure_date_col(df: pd.DataFrame, col: str = "date") -> pd.DataFrame:
    if col not in df.columns:
        if "InvoiceDate" in df.columns:
            df[col] = pd.to_datetime(df["InvoiceDate"]).dt.floor("d")
        elif "date" in df.columns:
            df[col] = pd.to_datetime(df["date"]).dt.floor("d")
        else:
            # try to infer index
            df = df.copy()
            df["date"] = pd.NaT
    else:
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.floor("d")
    return df

def bytes_for_df_csv(df: pd.DataFrame) -> bytes:
    b = df.to_csv(index=False).encode("utf-8")
    return b

# ---------- Load datasets ----------
st.set_page_config(layout="wide", page_title="E-commerce KPI Dashboard")
st.title("E-commerce KPI Dashboard — Project 2")

with st.spinner("Loading processed datasets ..."):
    daily = load_parquet_from_s3_or_local("daily")
    products = load_parquet_from_s3_or_local("products")
    rfm = load_parquet_from_s3_or_local("rfm")
    sample = load_parquet_from_s3_or_local("sample")
    metadata = load_json_from_s3_or_local("metadata")

# Show metadata if available
if metadata:
    st.sidebar.header("Dataset metadata")
    st.sidebar.json(metadata)

# ---------- Sidebar controls ----------
st.sidebar.header("Data source")
col_choice = st.sidebar.radio("Use data from:", ("S3 (BUCKET)", "Local ./data/processed"), index=0 if BUCKET else 1)
if col_choice == "Local ./data/processed":
    st.info("Using local ./data/processed files (LOCAL_OUT_DIR). Ensure preprocess.py has written outputs there.")
else:
    if not BUCKET:
        st.warning("No BUCKET configured. Set KPI_BUCKET env var or choose Local ./data/processed.")

# Date range filter (based on daily index)
daily = ensure_date_col(daily, "date")
if "date" in daily.columns and not daily["date"].isna().all():
    min_date = daily["date"].min()
    max_date = daily["date"].max()
    dr = st.sidebar.date_input("Date range", value=(min_date.date(), max_date.date()), min_value=min_date.date(), max_value=max_date.date())
    start_date, end_date = pd.to_datetime(dr[0]), pd.to_datetime(dr[1])
else:
    start_date, end_date = None, None

# ---------- Overview ----------
st.header("Overview")
col1, col2, col3, col4 = st.columns(4)

if not daily.empty:
    # apply date filter
    if start_date is not None:
        mask = (daily["date"] >= start_date) & (daily["date"] <= end_date)
        daily_f = daily.loc[mask].copy()
    else:
        daily_f = daily.copy()

    total_revenue = daily_f["operational_revenue"].sum()
    total_transactions = daily_f["transactions"].sum() if "transactions" in daily_f.columns else daily_f["tx_operational"].sum() if "tx_operational" in daily_f.columns else 0
    aov = daily_f["aov"].mean() if "aov" in daily_f.columns else (total_revenue / total_transactions if total_transactions else 0)

    col1.metric("Total revenue (filtered)", f"€{total_revenue:,.2f}")
    col2.metric("Transactions (filtered)", f"{int(total_transactions):,}")
    col3.metric("Avg order value (AOV)", f"€{aov:,.2f}")
    # cancellations if present
    if "cancellations" in daily_f.columns:
        col4.metric("Cancellations (days)", int((daily_f["cancellations"]>0).sum()))
    else:
        col4.write("")

    # Trend charts
    st.subheader("Trends")
    trend_cols = ["operational_revenue"]
    if "transactions" in daily_f.columns:
        trend_cols.append("transactions")
    df_trend = daily_f.set_index("date")[trend_cols].fillna(0)
    st.plotly_chart(px.line(df_trend.reset_index(), x="date", y=trend_cols, labels={"value":"amount","date":"Date"}), use_container_width=True)
else:
    st.warning("Daily KPIs not available. Run preprocess.py with --steps daily and ensure files are in out/ or S3.")

# ---------- Product analysis ----------
st.header("Product analysis")
if not products.empty:
    # show basic summary
    st.markdown("Top products (operational lines only). `is_meta` flags likely non-product/skus.")
    # Prepare display
    prod_df = products.copy()
    # optional filter to ignore meta SKUs
    show_meta = st.checkbox("Include meta / system SKUs (e.g. POST, DOT, short codes)", value=False)
    if not show_meta and "is_meta" in prod_df.columns:
        prod_df = prod_df[~prod_df["is_meta"]]

    top_n = st.slider("Top N products to show", 5, 50, 10)
    st.subheader("Top by revenue")
    top_rev = prod_df.sort_values("revenue", ascending=False).head(top_n)
    # show interactive table
    st.dataframe(top_rev[["StockCode" if "StockCode" in top_rev.columns else prod_df.columns[0], "description" if "description" in top_rev.columns else "desc_short" if "desc_short" in top_rev.columns else None, "revenue", "rev_share", "qty", "qty_share", "avg_price"]].rename(columns={None: "description"}), height=300)

    # Pareto / rev share chart
    st.subheader("Revenue share (Pareto)")
    pareto = prod_df.sort_values("revenue", ascending=False).head(100).copy()
    if not pareto.empty:
        pareto["cum_rev"] = pareto["revenue"].cumsum()
        pareto["cum_share"] = pareto["cum_rev"] / pareto["revenue"].sum()
        pareto["label"] = pareto.index.astype(str)
        fig = px.bar(pareto.head(20), x=pareto.head(20).index.astype(str), y="revenue", hover_data=["description", "rev_share"], labels={"x":"product","revenue":"Revenue"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Not enough product data to show pareto.")

    # Download top_n as CSV
    csv_bytes = bytes_for_df_csv(top_rev)
    st.download_button("Download top products CSV", data=csv_bytes, file_name="top_products_topn.csv", mime="text/csv")
else:
    st.warning("Products summary not available. Run preprocess.py with --steps products.")

# ---------- Customers / RFM ----------
st.header("Customer RFM analysis")
if not rfm.empty:
    rfm_df = rfm.copy()
    # defensive: ensure numeric columns
    for c in ["recency_days", "frequency", "monetary"]:
        if c in rfm_df.columns:
            rfm_df[c] = pd.to_numeric(rfm_df[c], errors="coerce").fillna(0)
    # RFM summary
    st.subheader("RFM segment counts")
    if "RFM_score" in rfm_df.columns:
        seg_counts = rfm_df["RFM_score"].value_counts().sort_index()
        st.bar_chart(seg_counts)
    else:
        st.write("RFM_score not found — showing percentiles.")
        st.dataframe(rfm_df.describe())

    st.subheader("Top customers by monetary value")
    top_customers = rfm_df.sort_values("monetary", ascending=False).head(20)
    st.dataframe(top_customers[["CustomerID" if "CustomerID" in top_customers.columns else None, "monetary", "frequency", "recency_days"]].rename(columns={None:"CustomerID"}), height=300)

    # download
    st.download_button("Download RFM CSV", data=bytes_for_df_csv(top_customers), file_name="top_customers.csv", mime="text/csv")
else:
    st.warning("RFM data not available. Run preprocess.py with --steps rfm and ensure CustomerID is present.")

# ---------- Data quality panel ----------
st.header("Data quality & diagnostics")
st.markdown("Quick checks based on `daily_kpis` and `sample_kpis`")

if not daily.empty:
    # zero-activity days in observed range
    overall_min = daily["date"].min()
    overall_max = daily["date"].max()
    full_range = pd.date_range(overall_min, overall_max, freq="D").date
    recorded = set(daily["date"].dt.date)
    missing = sorted(list(set(full_range) - recorded))
    st.write(f"Date range observed: **{overall_min.date()}** → **{overall_max.date()}**")
    st.write(f"Dates with ZERO recorded transactions between these dates: **{len(missing)}** (sample up to 10 below)")
    if missing:
        st.write(missing[:10])
else:
    st.write("No daily KPI data to assess coverage.")

if not sample.empty:
    st.subheader("Sample rows (operational / recent)")
    st.dataframe(sample.head(200), height=300)
    st.download_button("Download sample_kpis.csv", data=bytes_for_df_csv(sample), file_name="sample_kpis.csv", mime="text/csv")
else:
    st.write("No sample_kpis available.")

# ---------- Footer / help ----------
st.markdown("---")
st.markdown(
    "Notes: This dashboard reads processed outputs created by `preprocess.py` (daily_kpis.parquet, top_products_summary.parquet, rfm_customers.parquet, sample_kpis.csv). "
    "If any dataset is missing, run `python -m src.preprocess --raw ../data/raw/data.csv --out ./data/processed --steps all` (adjust paths) and upload `out/` to S3 or leave in local `./data/processed` directory."
)

st.markdown("**Tips for EC2 deployment:** create an IAM role for EC2 with `s3:GetObject`/`s3:ListBucket` on the bucket/prefix, install the Python deps, and run `streamlit run app.py --server.port 8501 --server.address 0.0.0.0`. Limit security group ingress to your IP for demos.")
