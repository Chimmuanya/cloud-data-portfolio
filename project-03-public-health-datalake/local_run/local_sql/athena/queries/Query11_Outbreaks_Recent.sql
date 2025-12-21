SELECT
  publication_date,
  title,
  source_url
FROM project03_db.who_outbreaks
ORDER BY publication_date DESC
LIMIT 20;
