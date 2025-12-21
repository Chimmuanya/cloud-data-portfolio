echo "ERROR: This script is deprecated."
echo "DuckDB analytics now rely on dataset-level views that mirror Athena tables."
echo "Directories like clean/who or clean/worldbank do not exist."
exit 1



#!/usr/bin/env bash
# scripts/utils/generate_duckdb_sql.sh
#
# Recreate DuckDB-compatible analytics SQL for local simulation
# Run from project root
#
# Output:
#   local_sql/duckdb/queries/*.sql

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="$ROOT_DIR/local_sql/duckdb/queries"

mkdir -p "$OUT_DIR"

echo "Generating DuckDB SQL → $OUT_DIR"
echo

# ------------------------------------------------------------
# Query 01 — Latest Life Expectancy
# ------------------------------------------------------------
cat > "$OUT_DIR/Query01_Latest_Life_Expectancy.sql" <<'SQL'
SELECT
  country_code,
  year,
  value AS life_expectancy
FROM read_parquet('local_data/clean/who/**/*.parquet')
WHERE indicator_code = 'WHOSIS_000001'
QUALIFY year = MAX(year) OVER ();
SQL

# ------------------------------------------------------------
# Query 02 — Top 20 Cholera Countries
# ------------------------------------------------------------
cat > "$OUT_DIR/Query02_Top20_Cholera.sql" <<'SQL'
SELECT
  country_code,
  SUM(value) AS cholera_cases
FROM read_parquet('local_data/clean/who/**/*.parquet')
WHERE indicator_code = 'CHOLERA_0000000001'
GROUP BY country_code
ORDER BY cholera_cases DESC
LIMIT 20;
SQL

# ------------------------------------------------------------
# Query 03 — Malaria YoY (Nigeria)
# ------------------------------------------------------------
cat > "$OUT_DIR/Query03_Malaria_YoY_NGA.sql" <<'SQL'
SELECT
  year,
  value AS malaria_incidence,
  value - LAG(value) OVER (ORDER BY year) AS yoy_change
FROM read_parquet('local_data/clean/who/**/*.parquet')
WHERE indicator_code = 'MALARIA_EST_INCIDENCE'
  AND country_code = 'NGA'
ORDER BY year;
SQL

# ------------------------------------------------------------
# Query 04 — Cholera vs Hospital Beds
# ------------------------------------------------------------
cat > "$OUT_DIR/Query04_Cholera_vs_Beds.sql" <<'SQL'
SELECT
  c.country_code,
  c.year,
  c.value AS cholera_cases,
  b.value AS beds_per_1000
FROM read_parquet('local_data/clean/who/**/*.parquet') c
JOIN read_parquet('local_data/clean/worldbank/**/*.parquet') b
  ON c.country_code = b.country_code
 AND c.year = b.year
WHERE c.indicator_code = 'CHOLERA_0000000001'
  AND b.indicator_id = 'SH.MED.BEDS.ZS';
SQL

# ------------------------------------------------------------
# Query 05 — Outbreaks Timeline
# ------------------------------------------------------------
cat > "$OUT_DIR/Query05_Outbreaks_Timeline.sql" <<'SQL'
SELECT
  EXTRACT(year FROM publication_date) AS year,
  COUNT(*) AS outbreak_count
FROM read_parquet('local_data/clean/outbreaks/**/*.parquet')
GROUP BY year
ORDER BY year;
SQL

# ------------------------------------------------------------
# Query 06 — Recent Outbreaks with Malaria Context
# ------------------------------------------------------------
cat > "$OUT_DIR/Query06_RecentOutbreaks_with_Malaria.sql" <<'SQL'
SELECT
  o.title,
  o.publication_date,
  m.value AS malaria_incidence
FROM read_parquet('local_data/clean/outbreaks/**/*.parquet') o
LEFT JOIN read_parquet('local_data/clean/who/**/*.parquet') m
  ON EXTRACT(year FROM o.publication_date) = m.year
 AND o.country_code = m.country_code
 AND m.indicator_code = 'MALARIA_EST_INCIDENCE'
ORDER BY o.publication_date DESC;
SQL

# ------------------------------------------------------------
# Query 07 — Life Expectancy % Change (2000–2020)
# ------------------------------------------------------------
cat > "$OUT_DIR/Query07_LE_2000_2020_pctchange.sql" <<'SQL'
WITH base AS (
  SELECT
    country_code,
    year,
    value
  FROM read_parquet('local_data/clean/who/**/*.parquet')
  WHERE indicator_code = 'WHOSIS_000001'
    AND year IN (2000, 2020)
)
SELECT
  country_code,
  MAX(value) FILTER (year = 2020) AS le_2020,
  MAX(value) FILTER (year = 2000) AS le_2000,
  (le_2020 - le_2000) / le_2000 * 100 AS pct_change
FROM base
GROUP BY country_code;
SQL

# ------------------------------------------------------------
# Query 08 — Avg Malaria (Last 5 Years)
# ------------------------------------------------------------
cat > "$OUT_DIR/Query08_AvgMalaria_5yrs.sql" <<'SQL'
WITH recent AS (
  SELECT
    country_code,
    year,
    value
  FROM read_parquet('local_data/clean/who/**/*.parquet')
  WHERE indicator_code = 'MALARIA_EST_INCIDENCE'
)
SELECT
  country_code,
  AVG(value) AS avg_malaria_5yrs
FROM recent
WHERE year >= (SELECT MAX(year) - 4 FROM recent)
GROUP BY country_code
ORDER BY avg_malaria_5yrs DESC;
SQL

echo "DuckDB SQL generation complete ✅"
