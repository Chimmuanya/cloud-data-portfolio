# Project 08 — Intelligent Invoice Processor (Textract + Lambda + S3)

**Short description**
Upload invoice PDFs to S3; Lambda calls Textract to extract vendor, total, invoice date and appends structured data to a CSV in S3. Demonstrates managed AI integration for SME automation.

**AWS quick facts**
- Region: eu-west-1
- Free-tier friendly: Textract 1,000 pages/month (use small sample set)
- Use with caution: do not upload confidential invoices with PHI.

**Structure**
infra/           # SAM template for S3 trigger + Lambda + SNS

lambdas/         # textract_worker/

sample_invoices/ # small set of test invoices (5-10)

scripts/         # deploy.sh

diagrams/        # architecture

evidence/        # extracted CSV, sample Textract outputs

**How to run (summary)**
1. Deploy via SAM; set OUTPUT_BUCKET and SNS topic.
2. Upload sample_invoice.pdf to S3.
3. Lambda calls Textract, writes parsed fields to the CSV in S3 and publishes SNS summary.

**Evidence to collect**
- Textract job response (CloudWatch)
- Output CSV in S3
- SNS email summary

**Notes**
Limit testing to a handful of invoices to remain within the Textract free tier.
