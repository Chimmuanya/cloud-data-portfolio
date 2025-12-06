# Project 06 — AWS FinOps Resource Auditor

**Short description**
Nightly serverless auditor that checks an AWS account for wasteful resources (unattached EBS, old snapshots, idle EC2, unused EIPs) and sends an SNS report.

**AWS quick facts**
- Region: eu-west-1
- Free-tier friendly: Lambda, EventBridge, SNS
- Requires deploy-ci with read permissions for account resources (least-privilege recommended).

**Structure**
infra/           # SAM template (Lambda + EventBridge + SNS)

lambdas/         # auditor/app.py

scripts/         # deploy.sh

diagrams/        # architecture

evidence/        # sample nightly report (SNS payload)

**How to run (summary)**
1. Deploy via SAM with a role that allows boto3 read operations for EC2/EBS/S3/Snapshot.
2. Schedule with EventBridge (daily).
3. Subscribe an email to the SNS topic to receive reports.

**Evidence to collect**
- Sample SNS message showing detected waste
- Lambda CloudWatch logs
- IAM policy used by auditor (for review)

**Notes**
This project demonstrates operational maturity and cost-awareness. Document false positives and safe remediation steps.
