# src/dashboard/load_data.py

import pandas as pd
from typing import Dict

from common.config import ATHENA_EVIDENCE_DIR


# ─────────────────────────────────────────────────────────────
# Core loader
# ─────────────────────────────────────────────────────────────

def load_csv(pattern: str) -> pd.DataFrame:
    """
    Load the *latest* CSV matching a glob pattern
    from evidence/athena/.

    Matches Project 3's append-only evidence model.
    """
    files = sorted(ATHENA_EVIDENCE_DIR.glob(pattern))

    if not files:
        raise FileNotFoundError(
            f"No evidence files match pattern: {ATHENA_EVIDENCE_DIR}/{pattern}"
        )

    latest = files[-1]
    return pd.read_csv(latest)


# ─────────────────────────────────────────────────────────────
# Dataset registry for dashboard
# ─────────────────────────────────────────────────────────────

def load_all() -> Dict[str, pd.DataFrame]:
    """
    Load all datasets required by dashboard registry.

    Keys must match registry.py 'dataset' entries.
    """
    return {
        # WHO indicators
        "life_expectancy": load_csv("*LifeExpectancy*.csv"),
        "malaria_incidence": load_csv("*Malaria*.csv"),
        "cholera": load_csv("*Cholera*.csv"),

        # WHO outbreaks
        "outbreak_counts": load_csv("*Outbreak*.csv"),

        # World Bank capacity indicators
        "life_vs_physicians": load_csv("*Physicians*.csv"),
        "malaria_vs_capacity": load_csv("*Physicians*.csv"),

        # Pipeline / meta
        "pipeline_health": load_csv("*Pipeline*.csv"),
    }
