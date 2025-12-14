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
