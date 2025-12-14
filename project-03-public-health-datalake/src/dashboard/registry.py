# src/dashboard/registry.py

VISUALIZATIONS = [

# 1. LIFE EXPECTANCY TREND
{
  "id": "life_expectancy_trend",
  "factory": "line_chart",
  "dataset": "life_expectancy",
  "params": {
    "x": "year",
    "y": "life_expectancy",
    "color": "country_name",
    "title": "Life Expectancy Trends (2000–Present)",
    "y_label": "Years"
  }
},

# 2. MALARIA INCIDENCE HEATMAP
{
  "id": "malaria_heatmap",
  "factory": "heatmap",
  "dataset": "malaria_incidence",
  "params": {
    "title": "Malaria Incidence Heatmap (Cases per 1,000)"
  }
},

# 3. CHOLERA BURDEN VS DATA GAPS
{
  "id": "cholera_missingness",
  "factory": "dual_axis_bar_dot",
  "dataset": "cholera",
  "params": {
    "title": "Cholera Burden vs Reporting Gaps"
  }
},

# 4. OUTBREAK FREQUENCY OVER TIME
{
  "id": "outbreaks_over_time",
  "factory": "line_chart",
  "dataset": "outbreak_counts",
  "params": {
    "x": "year",
    "y": "outbreak_count",
    "title": "Disease Outbreaks Over Time",
    "y_label": "Number of Outbreaks"
  }
},

# 5. TOP 10 COUNTRIES BY MALARIA BURDEN
{
  "id": "top10_malaria",
  "factory": "scatter",  # rendered as horizontal dot-bar surrogate
  "dataset": "malaria_incidence",
  "params": {
    "x": "malaria_incidence",
    "y": "country_name",
    "title": "Top 10 Countries by Malaria Burden",
    "x_label": "Cases per 1,000",
    "y_label": "Country"
  }
},

# 6. LIFE EXPECTANCY VS PHYSICIANS
{
  "id": "life_vs_physicians",
  "factory": "scatter",
  "dataset": "life_vs_physicians",
  "params": {
    "x": "physicians_per_1000",
    "y": "life_expectancy",
    "size": "population",
    "title": "Life Expectancy vs Physician Density",
    "x_label": "Physicians per 1,000",
    "y_label": "Life Expectancy"
  }
},

# 7. MALARIA VS HEALTH CAPACITY
{
  "id": "malaria_vs_capacity",
  "factory": "scatter",
  "dataset": "malaria_vs_capacity",
  "params": {
    "x": "physicians_per_1000",
    "y": "malaria_incidence",
    "color": "region",
    "title": "Malaria Burden vs Health Capacity",
    "x_label": "Physicians per 1,000",
    "y_label": "Malaria Incidence"
  }
},

# 8. CHOLERA + OUTBREAK TIMELINE
{
  "id": "cholera_outbreak_timeline",
  "factory": "line_chart",
  "dataset": "cholera",
  "params": {
    "x": "year",
    "y": "cholera_cases",
    "title": "Cholera Trends vs Outbreak Reports",
    "y_label": "Reported Cholera Cases"
  }
},

# 9. REGIONAL COMPARISON (SMALL MULTIPLES SOURCE)
{
  "id": "regional_comparison",
  "factory": "line_chart",
  "dataset": "life_expectancy",
  "params": {
    "x": "year",
    "y": "life_expectancy",
    "color": "region",
    "title": "Regional Health Indicators Over Time",
    "y_label": "Average Value"
  }
},

# 10. PIPELINE HEALTH & DATA FRESHNESS
{
  "id": "pipeline_health",
  "factory": "line_chart",
  "dataset": "pipeline_health",
  "params": {
    "x": "last_ingestion",
    "y": "files_ingested",
    "title": "Pipeline Health & Data Freshness",
    "y_label": "Files Ingested"
  }
}

]
