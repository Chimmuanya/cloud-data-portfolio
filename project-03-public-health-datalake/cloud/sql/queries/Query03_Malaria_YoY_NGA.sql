-- Query03: Year-over-Year % change for MALARIA_EST_INCIDENCE for a country (replace 'NGA' if needed)
SELECT
  curr.country_code,
  curr.year,
  curr.value AS value_curr,
  prev.value AS value_prev,
  100.0 * (curr.value - prev.value) / NULLIF(prev.value,0) AS pct_change
FROM project03_db.who_indicators curr
LEFT JOIN project03_db.who_indicators prev
  ON curr.country_code = prev.country_code
  AND curr.indicator_code = prev.indicator_code
  AND curr.year = prev.year + 1
WHERE curr.indicator_code = 'MALARIA_EST_INCIDENCE'
  AND curr.country_code = 'NGA'
ORDER BY curr.year DESC
LIMIT 10;
