SELECT
  date_trunc('month', publication_date) AS month,
  COUNT(*) AS events
FROM project03_db.who_outbreaks
WHERE publication_date >= date_add('year', -3, CURRENT_DATE)
GROUP BY 1
ORDER BY 1;
