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
