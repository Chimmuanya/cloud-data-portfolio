-- Query05: Outbreaks timeline (monthly counts) for the past 3 years
SELECT date_trunc('month', from_iso8601_timestamp(publication_date)) AS month,
       count(*) AS events
FROM project03_db.who_outbreaks
WHERE publication_date IS NOT NULL
  AND from_iso8601_timestamp(publication_date) >= date_add('year', -3, current_timestamp)
GROUP BY date_trunc('month', from_iso8601_timestamp(publication_date))
ORDER BY month;
