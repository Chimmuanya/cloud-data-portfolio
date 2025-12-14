-- Query07: Percent change in life expectancy between 2000 and 2020
WITH le2000 AS (
  SELECT country_code, value AS le_2000 FROM project03_db.who_indicators
  WHERE indicator_code = 'WHOSIS_000001' AND year = 2000
),
le2020 AS (
  SELECT country_code, value AS le_2020 FROM project03_db.who_indicators
  WHERE indicator_code = 'WHOSIS_000001' AND year = 2020
)
SELECT l20.country_code,
       l20.le_2020,
       l00.le_2000,
       100.0 * (l20.le_2020 - l00.le_2000) / NULLIF(l00.le_2000,0) AS pct_change
FROM le2020 l20
LEFT JOIN le2000 l00 ON l20.country_code = l00.country_code
ORDER BY pct_change DESC
LIMIT 50;
