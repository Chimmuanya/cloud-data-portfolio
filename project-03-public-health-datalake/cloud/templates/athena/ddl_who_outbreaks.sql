-- DDL: WHO Disease Outbreak News (Parquet, partitioned by year)
CREATE EXTERNAL TABLE IF NOT EXISTS project03_db.who_outbreaks (
  outbreak_id        string,
  country            string,
  disease            string,
  title              string,
  summary            string,
  publication_date   timestamp,
  source_url         string
)
PARTITIONED BY (
  year               int
)
STORED AS PARQUET
LOCATION 's3://$CLEAN_BUCKET/clean/who_outbreaks/'
TBLPROPERTIES (
  'parquet.compression' = 'SNAPPY'
);
