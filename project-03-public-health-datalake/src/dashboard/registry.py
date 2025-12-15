VISUALIZATIONS = [

    # 1. GLOBAL LIFE EXPECTANCY
    {
        "id": "life_expectancy_trend",
        "factory": "line_chart",
        "dataset": "life_expectancy",
        "params": {
            "x": "year",
            "y": "value",
            "title": "Global Life Expectancy Trend (2000–Present)",
            "y_label": "Years"
        }
    },

    # 2. MALARIA HEATMAP
    {
        "id": "malaria_heatmap",
        "factory": "heatmap",
        "dataset": "malaria_incidence_top_countries",
        "params": {
            "title": "Malaria Incidence Trends — Top 5 Countries"
        }
    },

    # 3. MALARIA TRENDS (LINES)
    {
        "id": "malaria_trends_top",
        "factory": "line_chart",
        "dataset": "malaria_incidence_top_countries",
        "params": {
            "x": "year",
            "y": "value",
            "color": "country_code",
            "title": "Malaria Incidence Over Time (Top 5 Countries)",
            "y_label": "Cases per 1,000"
        }
    },

    # 4. NIGERIA PHYSICIANS
    {
        "id": "nigeria_physicians",
        "factory": "line_chart",
        "dataset": "nigeria_physicians",
        "params": {
            "x": "year",
            "y": "value",
            "title": "Physician Density in Nigeria",
            "y_label": "Physicians per 1,000"
        }
    },

    # 5. NIGERIA VS SSA LIFE EXPECTANCY (FIXED, EXPLICIT)
    {
        "id": "nigeria_vs_ssa_life_expectancy",
        "factory": "nigeria_vs_ssa_life_expectancy",

        "datasets": {
            "countries": "life_expectancy_ssa",
            "reference": "life_expectancy_ssa_avg"
        },

        "params": {
            "highlight_country": "NGA",
            "peer_region": "Sub-Saharan Africa",
            "year_range": [2000, 2022],
            "title": "Life Expectancy: Nigeria vs Sub-Saharan Africa Average",
            "y_label": "Life Expectancy (Years)",
            "show_peer_background": True,
            "show_reference_line": True
        }
    },
]
