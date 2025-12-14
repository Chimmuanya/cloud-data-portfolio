SELECT
  country_code,
  SUM(value) AS cholera_cases
FROM read_parquet('local_data/clean/who/**/*.parquet')
WHERE indicator_code = 'CHOLERA_0000000001'
GROUP BY country_code
ORDER BY cholera_cases DESC
LIMIT 20;
