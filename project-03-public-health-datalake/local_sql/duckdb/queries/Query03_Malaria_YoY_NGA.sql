SELECT
  year,
  value AS malaria_incidence,
  value - LAG(value) OVER (ORDER BY year) AS yoy_change
FROM read_parquet('local_data/clean/who/**/*.parquet')
WHERE indicator_code = 'MALARIA_EST_INCIDENCE'
  AND country_code = 'NGA'
ORDER BY year;
