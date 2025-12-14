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
