# Project 05 — Containerized ML Inference API (Churn Model)

**Short description**
Deploy a small, trained churn prediction model as a containerized AWS Lambda image and expose it via API Gateway. Demonstrates MLOps and serverless inference.

**AWS quick facts**
- Region: eu-west-1
- Free-tier friendly: Lambda (1M requests), ECR (500MB free), API Gateway (1M calls)
- Keep model small (joblib / sklearn) to remain free-tier safe.

**Structure**
model/           # sample_model.joblib

src/             # handler.py

docker/          # Dockerfile for Lambda image

infra/           # SAM template using ImageUri

scripts/         # build-and-push.sh, deploy.sh

diagrams/        # architecture

evidence/        # test curl outputs, logs

**How to run (summary)**
1. Train model locally and save to model/sample_model.joblib.
2. Build container (scripts/build-and-push.sh) -> push to ECR.
3. Deploy via SAM (infra/template.yml) and configure API Gateway.
4. Test with `curl` to the API endpoint for inference.

**Evidence to collect**
- ECR image listed (describe-images)
- AWS Lambda configuration (image URI)
- API Gateway invocation logs
- Sample inference request/response

**Notes**
Use small models. If you later need larger inference workloads, document the trade-offs and cost implications.
