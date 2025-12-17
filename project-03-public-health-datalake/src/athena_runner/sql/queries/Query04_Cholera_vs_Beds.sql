-- Query04: Top countries with high cholera cases & low hospital-beds (World Bank indicator SH.MED.BEDS.ZS)
WITH cholera_latest AS (
  SELECT c.country_code, c.year, c.value
  FROM (
    SELECT country_code, MAX(year) AS year
    FROM project03_db.who_indicators
    WHERE indicator_code = 'CHOLERA_0000000001'
    GROUP BY country_code
  ) latest
  JOIN project03_db.who_indicators c
    ON c.country_code = latest.country_code AND c.year = latest.year
    AND c.indicator_code = 'CHOLERA_0000000001'
),
beds_latest AS (
  SELECT w.country_code, w.year, w.value AS beds_per_1000
  FROM (
    SELECT country_code, MAX(year) AS year
    FROM project03_db.worldbank_indicators
    WHERE indicator_id = 'SH.MED.BEDS.ZS'
    GROUP BY country_code
  ) lb
  JOIN project03_db.worldbank_indicators w
    ON w.country_code = lb.country_code AND w.year = lb.year
    AND w.indicator_id = 'SH.MED.BEDS.ZS'
)
SELECT ch.country_code,
       ch.year AS cholera_year, ch.value AS cholera_cases,
       b.beds_per_1000
FROM cholera_latest ch
LEFT JOIN beds_latest b ON ch.country_code = b.country_code
ORDER BY ch.value DESC
LIMIT 50;
