-- Query01: Latest life expectancy per country (indicator WHOSIS_000001)
WITH parts AS (
  SELECT * FROM project03_db.who_indicators
  WHERE indicator_code = 'WHOSIS_000001'
)
SELECT w.country_code, w.year, w.value
FROM (
  SELECT country_code, MAX(year) AS year FROM parts GROUP BY country_code
) latest
JOIN parts w
  ON w.country_code = latest.country_code AND w.year = latest.year
ORDER BY w.value DESC
LIMIT 100;
