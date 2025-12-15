from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from common.config import DASHBOARD_EVIDENCE_DIR
from common.logging import setup_logging

from charts import (
    line_chart,
    heatmap,
    nigeria_vs_ssa_life_expectancy,
)
from registry import VISUALIZATIONS
from load_data import load_all

logger = setup_logging(__name__)

FACTORIES = {
    "line_chart": line_chart,
    "heatmap": heatmap,
    "nigeria_vs_ssa_life_expectancy": nigeria_vs_ssa_life_expectancy,
}


def get_output_dir() -> Path:
    DASHBOARD_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    return DASHBOARD_EVIDENCE_DIR


def render_dashboard(figures: List[Dict]) -> str:
    sections = []

    for item in figures:
        sections.append(
            f"""
            <section class="chart-block">
              <h2>{item['title']}</h2>
              {item['figure'].to_html(full_html=False, include_plotlyjs="cdn")}
            </section>
            """
        )

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Project 3 — Public Health Dashboard</title>
  <style>
    body {{ font-family: system-ui; margin: 40px; background: #fafafa; }}
    .chart-block {{ margin-bottom: 70px; border-bottom: 1px solid #ddd; }}
  </style>
</head>
<body>
  <h1>Public Health Indicators Dashboard</h1>
  {''.join(sections)}
</body>
</html>
"""


def build_dashboard() -> Path:
    datasets = load_all()
    figures = []

    for viz in VISUALIZATIONS:
        factory = FACTORIES[viz["factory"]]
        params = viz.get("params", {})

        # SINGLE DATASET
        if "dataset" in viz:
            df = datasets[viz["dataset"]]
            fig = factory(df, **params)

        # MULTI DATASET (Chart 5)
        else:
            bound = {
                role: datasets[name]
                for role, name in viz["datasets"].items()
            }
            fig = factory(**bound, **params)

        figures.append({
            "id": viz["id"],
            "title": params.get("title", viz["id"]),
            "figure": fig,
        })

    html = render_dashboard(figures)

    out = get_output_dir() / f"dashboard_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.html"
    out.write_text(html, encoding="utf-8")

    logger.info("Dashboard written → %s", out)
    return out


if __name__ == "__main__":
    build_dashboard()
