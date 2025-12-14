-- WHO indicators (Parquet, partitioned)
CREATE EXTERNAL TABLE IF NOT EXISTS project03_db.who_indicators (
  country_code     string,
  value            double
)
PARTITIONED BY (
  indicator_code   string,
  year             int
)
STORED AS PARQUET
LOCATION 's3://<CLEAN_BUCKET>/clean/who_indicators/'
TBLPROPERTIES (
  'parquet.compression' = 'SNAPPY'
);
