# Project 03 — Public Health Serverless Data Lake & Dashboard

**Short description**
Serverless ingestion (EventBridge → Lambda) writes raw public health data to S3 (partitioned). Glue Crawler + Athena used for analytics. Minimal dashboard runs on EC2 or S3 static site.

**AWS quick facts**
- Region: eu-west-1
- Free-tier friendly: Lambda (1M invocations), S3 (5GB), Athena (tiny data scans)
- Ingest cadence: weekly (EventBridge)

**Structure**
infra/           # SAM template (Lambda, EventBridge rule, S3)

lambdas/         # ingest lambda code

analytics/       # sample Athena queries

scripts/         # deploy.sh, glue_setup.sh

sample/          # sample WHO/CDC JSONs

diagrams/        # architecture

evidence/        # ingestion logs + outputs

**How to run (summary)**
1. Configure `deploy-ci` profile with your AWS keys.
2. Edit `infra/template.yml` to set `RAW_BUCKET` and stack name.
3. `sam build && sam deploy --guided` (eu-west-1).
4. Verify raw files in `s3://<RAW_BUCKET>/public-health/raw/...`.
5. Create Glue crawler (scripts/glue_setup.sh) and run sample Athena queries.

**Evidence to collect**
- CloudWatch logs for ingestion Lambda
- S3 listing of raw/processed files
- Athena query results (saved to S3)
- Screenshot of Streamlit dashboard or static site

**Notes**
Use WHO/CDC open APIs and keep raw data sizes small. This project demonstrates a proper data-lake pattern.
