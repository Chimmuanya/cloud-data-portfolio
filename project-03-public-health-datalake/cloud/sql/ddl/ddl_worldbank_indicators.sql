CREATE OR REPLACE VIEW project03_db.worldbank_indicators AS
SELECT country_code, indicator_id, year, value
FROM project03_db.wb_hospital_beds_per_1000

UNION ALL
SELECT country_code, indicator_id, year, value
FROM project03_db.wb_physicians_per_1000;
