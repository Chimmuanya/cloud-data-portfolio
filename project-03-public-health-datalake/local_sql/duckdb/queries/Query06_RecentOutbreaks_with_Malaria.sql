SELECT
  o.title,
  o.publication_date,
  m.value AS malaria_incidence
FROM read_parquet('local_data/clean/outbreaks/**/*.parquet') o
LEFT JOIN read_parquet('local_data/clean/who/**/*.parquet') m
  ON EXTRACT(year FROM o.publication_date) = m.year
 AND o.country_code = m.country_code
 AND m.indicator_code = 'MALARIA_EST_INCIDENCE'
ORDER BY o.publication_date DESC;
