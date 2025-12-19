CREATE EXTERNAL TABLE IF NOT EXISTS project03_db.life_expectancy (
  country_code string,
  indicator_code string,
  value double
)
PARTITIONED BY (year int)
STORED AS PARQUET
LOCATION 's3://<CLEAN_BUCKET>/clean/life_expectancy/'
TBLPROPERTIES (
  'projection.enabled' = 'true',
  'projection.year.type' = 'integer',
  'projection.year.range' = '2000,2025',
  'storage.location.template' =
    's3://<CLEAN_BUCKET>/clean/life_expectancy/year=${year}'
);
