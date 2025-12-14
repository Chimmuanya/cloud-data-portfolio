SELECT
  country_code,
  year,
  value AS life_expectancy
FROM read_parquet('local_data/clean/who/**/*.parquet')
WHERE indicator_code = 'WHOSIS_000001'
QUALIFY year = MAX(year) OVER ();
