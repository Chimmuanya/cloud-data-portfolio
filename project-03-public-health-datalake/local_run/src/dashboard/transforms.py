import pandas as pd
from typing import Iterable


# ─────────────────────────────────────────────────────────────
# Remove non-country aggregates
# ─────────────────────────────────────────────────────────────
def drop_aggregates(
    df: pd.DataFrame,
    *,
    country_col: str = "country_code",
    aggregate_codes: Iterable[str] = ("WLD", "OWID", "AFR", "EUU", "ARB")
) -> pd.DataFrame:
    """
    Remove aggregate / regional rows.

    Default codes cover:
    - World (WLD)
    - OWID synthetic aggregates
    - Africa (AFR)
    - EU aggregates (EUU)
    - Arab World (ARB)
    """
    if country_col not in df.columns:
        return df

    mask = ~df[country_col].astype(str).isin(aggregate_codes)
    return df.loc[mask].copy()


# ─────────────────────────────────────────────────────────────
# Enforce numeric columns safely
# ─────────────────────────────────────────────────────────────
def enforce_numeric(
    df: pd.DataFrame,
    cols: Iterable[str]
) -> pd.DataFrame:
    """
    Coerce selected columns to numeric.
    Invalid values become NaN (non-fatal).
    """
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


# ─────────────────────────────────────────────────────────────
# Filter to latest available year
# ─────────────────────────────────────────────────────────────
def latest_year(
    df: pd.DataFrame,
    *,
    year_col: str = "year"
) -> pd.DataFrame:
    """
    Return rows for the most recent year present in the data.
    """
    if year_col not in df.columns or df.empty:
        return df

    max_year = pd.to_numeric(df[year_col], errors="coerce").max()
    return df[df[year_col] == max_year].copy()
