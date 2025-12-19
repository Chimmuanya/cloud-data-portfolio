CREATE OR REPLACE VIEW project03_db.who_indicators AS
SELECT country_code, indicator_code, year, value
FROM project03_db.life_expectancy

UNION ALL
SELECT country_code, indicator_code, year, value
FROM project03_db.malaria_incidence

UNION ALL
SELECT country_code, indicator_code, year, value
FROM project03_db.cholera;
