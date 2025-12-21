import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

DEFAULT_THEME = "plotly_white"

# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------
def _require_columns(df: pd.DataFrame, required: list, chart_name: str):
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"{chart_name}: missing required columns: {missing}"
        )


def _clean_numeric(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.dropna(subset=cols)


# ------------------------------------------------------------------
# Generic line chart (USED BY CHARTS 1–4)
# ------------------------------------------------------------------
def line_chart(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    y_label: str,
    color: str | None = None,
):
    required = [x, y]
    if color:
        required.append(color)

    _require_columns(df, required, "line_chart")

    clean_df = _clean_numeric(df, [x, y])

    fig = px.line(
        clean_df,
        x=x,
        y=y,
        color=color,
    )

    fig.update_layout(
        title=title,
        xaxis_title=x.capitalize(),
        yaxis_title=y_label,
        template=DEFAULT_THEME,
    )

    return fig


# ------------------------------------------------------------------
# Chart 5 — Nigeria vs SSA life expectancy (SPECIAL CASE)
# ------------------------------------------------------------------
def nigeria_vs_ssa_life_expectancy(
    *,
    countries: pd.DataFrame,
    reference: pd.DataFrame,
    highlight_country: str,
    peer_region: str,
    year_range: list[int],
    title: str,
    y_label: str,
    show_peer_background: bool = True,
    show_reference_line: bool = True,
):
    required_cols = ["country_code", "year", "value"]
    _require_columns(countries, required_cols, "nigeria_vs_ssa_life_expectancy")
    _require_columns(reference, ["year", "ssa_avg"], "nigeria_vs_ssa_life_expectancy")

    start, end = year_range
    countries = countries[countries["year"].between(start, end)]
    reference = reference[reference["year"].between(start, end)]

    # 1. Initialize Figure
    fig = go.Figure()

    # 2. Optimized Peer Background (Vectorized)
    if show_peer_background:
        peers = countries[countries["country_code"] != highlight_country]

        # We use px.line just to generate the traces efficiently,
        # then we extract them and add them to our main figure.
        tmp_fig = px.line(
            peers,
            x="year",
            y="value",
            line_group="country_code",
            color_discrete_sequence=["rgba(180,180,180,0.3)"] # Light gray
        )

        for trace in tmp_fig.data:
            trace.showlegend = False
            trace.hoverinfo = "skip"
            trace.line.width = 1
            fig.add_trace(trace)

    # 3. Highlight Country (Nigeria)
    nga = countries[countries["country_code"] == highlight_country]
    fig.add_trace(
        go.Scatter(
            x=nga["year"],
            y=nga["value"],
            mode="lines+markers",
            name=highlight_country,
            line=dict(color="#d62728", width=4),
            marker=dict(size=8),
        )
    )

    # 4. Reference Line (SSA Average)
    if show_reference_line:
        fig.add_trace(
            go.Scatter(
                x=reference["year"],
                y=reference["ssa_avg"],
                mode="lines",
                name=f"{peer_region} Avg",
                line=dict(color="#1f77b4", width=3, dash="dash"),
            )
        )

    # ... update_layout remains the same ...
    fig.update_layout(
        title=title,
        xaxis_title="Year",
        yaxis_title=y_label,
        template=DEFAULT_THEME,
        legend=dict(
            orientation="h",
            y=1.05,
            x=0,
        ),
        margin=dict(l=60, r=40, t=80, b=60),
    )

    return fig


# ------------------------------------------------------------------
# Heatmap
# ------------------------------------------------------------------
def heatmap(
    df: pd.DataFrame,
    *,
    title: str,
    index_col: str = "country_code",
    column_col: str = "year",
    value_col: str = "value",
):
    _require_columns(df, [index_col, column_col, value_col], "heatmap")

    clean_df = _clean_numeric(df, [column_col, value_col])

    pivot = (
        clean_df
        .pivot_table(
            index=index_col,
            columns=column_col,
            values=value_col,
            aggfunc="mean",
        )
        .sort_index(axis=1)
    )

    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale="YlOrRd",
    )

    fig.update_layout(
        title=title,
        template=DEFAULT_THEME,
        coloraxis_colorbar_title="Value",
        xaxis_title="Year",
        yaxis_title="Country",
    )

    return fig
