CREATE EXTERNAL TABLE IF NOT EXISTS project03_db.wb_hospital_beds_per_1000 (
  country_code string,
  indicator_id string,
  value double
)
PARTITIONED BY (year int)
STORED AS PARQUET
LOCATION 's3://<CLEAN_BUCKET>/clean/wb_hospital_beds_per_1000/';
