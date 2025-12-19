CREATE EXTERNAL TABLE IF NOT EXISTS project03_db.who_outbreaks (
  outbreak_id        string,
  title              string,
  summary            string,
  publication_date   timestamp,
  source_url         string
)
PARTITIONED BY (
  year int
)
STORED AS PARQUET
LOCATION 's3://<CLEAN_BUCKET>/clean/who_outbreaks/'
TBLPROPERTIES (
  'parquet.compression'='SNAPPY',
  'projection.enabled'='true',
  'projection.year.type'='integer',
  'projection.year.range'='2000,2030',
  'storage.location.template'='s3://<CLEAN_BUCKET>/clean/who_outbreaks/year=${year}'
);
