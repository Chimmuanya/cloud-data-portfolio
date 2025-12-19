SELECT
  LOWER(title) AS title_text,
  COUNT(*) AS occurrences
FROM project03_db.who_outbreaks
GROUP BY LOWER(title)
ORDER BY occurrences DESC
LIMIT 20;
