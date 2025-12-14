"""
src/dashboard/build.py

Registry-driven dashboard builder for Project 3.

- Local-first
- Cloud-compatible
- Produces static HTML artifact
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from charts import (
    line_chart,
    heatmap,
    scatter,
    dual_axis_bar_dot,
)
from registry import VISUALIZATIONS
from load_data import load_all
from layout import render_dashboard

from common.config import DASHBOARD_EVIDENCE_DIR
from common.logging import setup_logging


# ─────────────────────────────────────────────────────────────
# Logging (centralized)
# ─────────────────────────────────────────────────────────────
logger = setup_logging(__name__)


# ─────────────────────────────────────────────────────────────
# Chart factory registry
# ─────────────────────────────────────────────────────────────
FACTORIES = {
    "line_chart": line_chart,
    "heatmap": heatmap,
    "scatter": scatter,
    "dual_axis_bar_dot": dual_axis_bar_dot,
}


# ─────────────────────────────────────────────────────────────
# Output paths (Project 3 standard)
# ─────────────────────────────────────────────────────────────

def get_output_dir() -> Path:
    """
    Dashboard artifacts go to:
      evidence/dashboard/
    """
    DASHBOARD_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    return DASHBOARD_EVIDENCE_DIR


# ─────────────────────────────────────────────────────────────
# Core build logic
# ─────────────────────────────────────────────────────────────

def build_dashboard() -> Path:
    """
    Build all visualizations and write a single HTML dashboard.
    Returns path to generated HTML file.
    """
    logger.info("Loading datasets for dashboard")
    dataframes: Dict[str, object] = load_all()

    figures = []

    logger.info("Building visualizations (%d total)", len(VISUALIZATIONS))
    for viz in VISUALIZATIONS:
        viz_id = viz["id"]
        factory_name = viz["factory"]
        dataset_name = viz["dataset"]

        if factory_name not in FACTORIES:
            raise ValueError(f"Unknown chart factory: {factory_name}")

        if dataset_name not in dataframes:
            raise ValueError(f"Dataset not loaded: {dataset_name}")

        factory = FACTORIES[factory_name]
        df = dataframes[dataset_name]

        logger.info("  • %s", viz_id)
        fig = factory(df, **viz["params"])
        figures.append({
            "id": viz_id,
            "figure": fig,
            "title": viz["params"].get("title", viz_id),
        })

    html = render_dashboard(figures)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_file = get_output_dir() / f"dashboard_{ts}.html"

    out_file.write_text(html, encoding="utf-8")

    logger.info("Dashboard written → %s", out_file.resolve())
    return out_file


# ─────────────────────────────────────────────────────────────
# CLI / Lambda entrypoint
# ─────────────────────────────────────────────────────────────

def main():
    """
    Local usage:
      python src/dashboard/build.py

    Cloud usage:
      called from Lambda / batch job
    """
    build_dashboard()


if __name__ == "__main__":
    main()
