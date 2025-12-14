# src/dashboard/charts.py

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

DEFAULT_THEME = "plotly_white"


# ─────────────────────────────────────────────────────────────
# Line chart (time series, trends)
# ─────────────────────────────────────────────────────────────
def line_chart(
    df,
    *,
    x,
    y,
    color=None,
    title,
    y_label,
):
    fig = px.line(
        df,
        x=x,
        y=y,
        color=color,
        hover_data={
            x: True,
            y: ":.2f"
        },
    )
    fig.update_layout(
        title=title,
        xaxis_title=x.capitalize(),
        yaxis_title=y_label,
        template=DEFAULT_THEME,
        legend_title_text=color.capitalize() if color else None,
    )
    return fig


# ─────────────────────────────────────────────────────────────
# Heatmap (burden distribution)
# ─────────────────────────────────────────────────────────────
def heatmap(
    df,
    *,
    title,
):
    fig = px.imshow(
        df,
        color_continuous_scale="YlOrRd",
        aspect="auto",
    )
    fig.update_layout(
        title=title,
        template=DEFAULT_THEME,
        coloraxis_colorbar_title="Value",
    )
    return fig


# ─────────────────────────────────────────────────────────────
# Scatter (capacity vs outcome)
# ─────────────────────────────────────────────────────────────
def scatter(
    df,
    *,
    x,
    y,
    size=None,
    color=None,
    title,
    x_label,
    y_label,
):
    fig = px.scatter(
        df,
        x=x,
        y=y,
        size=size,
        color=color,
        hover_name="country_name",
        trendline="lowess",
    )
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        template=DEFAULT_THEME,
        legend_title_text=color.capitalize() if color else None,
    )
    return fig


# ─────────────────────────────────────────────────────────────
# Dual-axis bar + dot (data quality view)
# ─────────────────────────────────────────────────────────────
def dual_axis_bar_dot(
    df,
    *,
    title,
):
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_bar(
        x=df["country_name"],
        y=df["cholera_cases"],
        name="Reported Cholera Cases",
    )

    fig.add_scatter(
        x=df["country_name"],
        y=df["missing_fraction"],
        name="Missing Data Fraction",
        mode="markers",
        secondary_y=True,
    )

    fig.update_layout(
        title=title,
        template=DEFAULT_THEME,
        legend_title_text="Metric",
    )

    fig.update_yaxes(
        title_text="Reported Cholera Cases",
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Missing Fraction",
        secondary_y=True,
        tickformat=".0%",
    )

    return fig
