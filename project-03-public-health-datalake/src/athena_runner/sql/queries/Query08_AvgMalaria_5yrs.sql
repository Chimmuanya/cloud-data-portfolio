-- Query08: Rank countries by average malaria incidence over last 5 years
WITH recent AS (
  SELECT country_code, year, value
  FROM project03_db.malaria_incidence
  WHERE indicator_code = 'MALARIA_EST_INCIDENCE'
    AND year >= year(current_date) - 5
)
SELECT country_code,
       AVG(value) AS avg_malaria
FROM recent
GROUP BY country_code
ORDER BY avg_malaria DESC
LIMIT 25;
