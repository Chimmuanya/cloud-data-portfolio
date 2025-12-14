SELECT
  EXTRACT(year FROM publication_date) AS year,
  COUNT(*) AS outbreak_count
FROM read_parquet('local_data/clean/outbreaks/**/*.parquet')
GROUP BY year
ORDER BY year;
