# Project 04 — Serverless Radiology DICOM Metadata ETL Pipeline

**Short description**
Event-driven pipeline: upload DICOM to S3 -> Lambda (pydicom layer) extracts metadata -> DynamoDB stores metadata -> API Gateway exposes queries. This is metadata-only (no pixel data).

**AWS quick facts**
- Region: eu-west-1
- Free-tier friendly: S3, Lambda, DynamoDB (25GB)
- IMPORTANT: Do not store pixel/PHI. Use synthetic or TCIA public metadata.

**Structure**
infra/           # SAM template (S3 trigger, Lambda, DynamoDB, API)

lambdas/         # extractor/ and api/ handlers

sample/          # sample_dicom_metadata.json (NOT pixel data)

scripts/         # layer_build.sh, deploy.sh, capture-evidence.sh

diagrams/        # architecture (draw.io)

evidence/        # DynamoDB items export, CloudWatch logs

**How to run (summary)**
1. Build or use a pydicom Lambda layer (infra/layer_build.sh).
2. `sam build && sam deploy --guided` (set bucket and table names).
3. Upload sample metadata JSONs or small DICOMs (metadata only) to `s3://<BUCKET>/raw/`.
4. Confirm DynamoDB received records and test API queries.

**Evidence to collect**
- S3 object listing (raw/)
- CloudWatch logs showing extraction for specific object
- DynamoDB query results
- API Gateway sample GET response

**Notes**
Emphasize metadata-only processing in README and in evidence. This keeps the project compliant and sharable.
