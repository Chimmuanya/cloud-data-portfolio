-- Query06: Latest outbreaks with country & matching indicator (malaria)
WITH malaria_latest AS (
  SELECT m.country_code, m.year, m.value AS malaria_value
  FROM (
    SELECT country_code, MAX(year) AS year
    FROM project03_db.who_indicators
    WHERE indicator_code = 'MALARIA_EST_INCIDENCE'
    GROUP BY country_code
  ) lm
  JOIN project03_db.who_indicators m
    ON m.country_code = lm.country_code AND m.year = lm.year
    AND m.indicator_code = 'MALARIA_EST_INCIDENCE'
),
recent_outbreaks AS (
  SELECT *
  FROM project03_db.who_outbreaks
  WHERE publication_date IS NOT NULL
    AND publication_date >= date_add('day', -90, current_timestamp)
)
SELECT r.publication_date, r.title, r.country_iso, ml.malaria_value
FROM recent_outbreaks r
LEFT JOIN malaria_latest ml ON ml.country_code = r.country_iso
ORDER BY r.publication_date DESC
LIMIT 200;
