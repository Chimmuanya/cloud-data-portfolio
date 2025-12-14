-- Query02: Top 20 countries by Cholera (most recent year)
WITH cholera AS (
  SELECT * FROM project03_db.who_indicators WHERE indicator_code = 'CHOLERA_0000000001'
),
latest AS (
  SELECT country_code, MAX(year) AS year
  FROM cholera
  GROUP BY country_code
)
SELECT c.country_code, c.year, c.value
FROM cholera c
JOIN latest l
  ON c.country_code = l.country_code AND c.year = l.year
ORDER BY c.value DESC
LIMIT 20;
