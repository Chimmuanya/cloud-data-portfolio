#!/usr/bin/env bash
# scripts/bootstrap-repo-infra-and-projects.sh
#
# Purpose:
#   Create repo-level infra (bootstrap, shared-policies, ci/templates)
#   and project-level scaffolds for project-02 .. project-08.
#
# Behavior:
#   - Idempotent: will not overwrite existing files unless --force is passed.
#   - Creates per-project infra/ plus src/, scripts/, diagrams/exported/, evidence/, sample/.
#   - Writes useful placeholder files (README.md, infra/template.yml, basic bootstrap/policies).
#
# Usage:
#   ./scripts/bootstrap-repo-infra-and-projects.sh [--force]
#
# Options:
#   --force  Overwrite existing files (README.md and infra placeholders).
#   -h|--help  Show help
#
# Suggested atomic commit message after review:
#   chore(repo): add global infra and project-02..project-08 scaffolds with placeholders
set -euo pipefail

FORCE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1; shift ;;
    -h|--help)
      cat <<EOF
Usage: $0 [--force]
Creates global infra/ (bootstrap, shared-policies, ci/templates) and project scaffolds (project-02..project-08).
--force: overwrite existing placeholder files (README.md, infra/template.yml, global infra placeholders)
EOF
      exit 0
      ;;
    *)
      echo "Unknown arg: $1"
      exit 1
      ;;
  esac
done

ROOT_DIR="$(pwd)"
echo "Repository root: ${ROOT_DIR}"
DEFAULT_REGION="eu-west-1"
DEFAULT_PROFILE="deploy-ci"

# Helpers
mkdir_p() {
  if [ ! -d "$1" ]; then
    mkdir -p "$1"
    echo "created dir: $1"
  else
    echo "exists dir:  $1"
  fi
}

write_file() {
  # write_file <path> <heredoc_content>
  local path="$1"
  shift
  local content="$*"
  if [ -f "${path}" ] && [ "${FORCE}" -ne 1 ]; then
    echo "skip (exists): ${path}"
    return 0
  fi
  printf '%s\n' "${content}" > "${path}"
  echo "wrote: ${path}"
}

# 1) Create global infra folders
echo; echo ">>> Creating global infra structure"
mkdir_p "infra"
mkdir_p "infra/bootstrap"
mkdir_p "infra/shared-policies"
mkdir_p "infra/ci/templates"
mkdir_p "infra/modules" || true

# 1a) Write a safe placeholder for create-deploy-ci.sh
BOOTSTRAP_SH="infra/bootstrap/create-deploy-ci.sh"
write_file "${BOOTSTRAP_SH}" "#!/usr/bin/env bash
# infra/bootstrap/create-deploy-ci.sh
# Purpose: (TEMPLATE) Create deploy-ci user, packaging S3 bucket and base policies.
# IMPORTANT: This is a template. Review and run with an administrative account.
# Usage: bash create-deploy-ci.sh <account-id> <region> <packaging-bucket-name>
set -euo pipefail

ACCOUNT_ID=\${1:-<AWS_ACCOUNT_ID>}
REGION=\${2:-${DEFAULT_REGION}}
PACKAGING_BUCKET=\${3:-<my-sam-packaging-bucket-\${ACCOUNT_ID}>\}

echo \"This script is a template. Replace placeholders and run with admin credentials.\"
echo \"Example: \"
echo \"  bash create-deploy-ci.sh 123456789012 ${DEFAULT_REGION} my-sam-packaging-bucket-123456789012\"

# TODO:
#  - Create deploy-ci IAM user with programmatic access
#  - Create packaging S3 bucket with block public access and encryption
#  - Create minimal policies in infra/shared-policies and attach to deploy-ci
#  - Store access keys securely (not in repo)
"

chmod_if_needed() {
  if [ -f "$1" ]; then
    chmod 0755 "$1" || true
  fi
}
chmod_if_needed "${BOOTSTRAP_SH}"

# 1b) Write a placeholder least-privilege deploy-ci policy
DEPLOY_POLICY="infra/shared-policies/deploy-ci-policy.json"
write_file "${DEPLOY_POLICY}" '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3PackageUpload",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::<YOUR_PACKAGING_BUCKET>",
        "arn:aws:s3:::<YOUR_PACKAGING_BUCKET>/*"
      ]
    },
    {
      "Sid": "AllowCloudFormationDeploy",
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateStack",
        "cloudformation:DescribeStacks",
        "cloudformation:UpdateStack",
        "cloudformation:DeleteStack",
        "cloudformation:DescribeStackEvents",
        "cloudformation:ListStackResources"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowECRPush",
      "Effect": "Allow",
      "Action": [
        "ecr:CreateRepository",
        "ecr:BatchCheckLayerAvailability",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    }
  ]
}'

# 1c) CI template placeholder
CI_TEMPLATE="infra/ci/templates/deploy-sam-template.yml"
write_file "${CI_TEMPLATE}" "# infra/ci/templates/deploy-sam-template.yml
# This is a CI job template placeholder. In your GitHub Actions workflows, import or copy this
# and set PROJECT_NAME / STACK_NAME / AWS_REGION / AWS_PROFILE / S3_BUCKET variables.
# Keep secrets in GitHub Secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_PROFILE)

name: Deploy SAM - \${{ matrix.project }}
on:
  workflow_dispatch:
  push:
    paths:
      - 'project-*/infra/**'
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up AWS CLI
        run: sudo apt-get update && sudo apt-get install -y awscli
      - name: SAM Build & Deploy (placeholder)
        run: |
          echo \"Replace this step with your sam build & sam deploy commands for the target project.\"
"

# 2) Create per-project scaffolds (project-02 .. project-08)
echo; echo ">>> Creating project scaffolds (project-02 .. project-08)"
declare -A PROJECT_NAMES
PROJECT_NAMES[2]="kpi-dashboard"
PROJECT_NAMES[3]="public-health-datalake"
PROJECT_NAMES[4]="radiology-dicom-etl"
PROJECT_NAMES[5]="ml-inference-api"
PROJECT_NAMES[6]="finops-auditor"
PROJECT_NAMES[7]="hospital-queue-simulator"
PROJECT_NAMES[8]="invoice-idp"

for idx in 2 3 4 5 6 7 8; do
  num=$(printf "%02d" "${idx}")
  slug="${PROJECT_NAMES[$idx]}"
  proj="project-${num}-${slug}"
  echo "--- ${proj}"

  # Create standard subfolders
  mkdir_p "${proj}"
  mkdir_p "${proj}/infra"
  mkdir_p "${proj}/src"
  mkdir_p "${proj}/scripts"
  mkdir_p "${proj}/diagrams"
  mkdir_p "${proj}/diagrams/exported"
  mkdir_p "${proj}/evidence"
  mkdir_p "${proj}/sample"

  # Write project-specific README (do not clobber unless FORCE)
  README_PATH="${proj}/README.md"
  case "${idx}" in
    2)
      content="# Project ${num} — Multi-Sector KPI Business Dashboard (EC2 + S3 + Athena)

**Short description**
Host a Streamlit KPI dashboard on an EC2 t2.micro instance that queries Athena over S3 data. Demonstrates cloud-hosted BI using AWS Free Tier resources.

**Quickstart**
1. Edit \`infra/\` scripts to set \`<YOUR_DATA_BUCKET>\` and key pair name.
2. Run \`bash infra/ec2_launch.sh <key-name> <deploy-profile>\`.
3. SSH into EC2 and run the Streamlit app.

**Evidence**
- EC2 instance listing, Streamlit web screenshot, Athena query result, S3 data listing.
"
      ;;
    3)
      content="# Project ${num} — Public Health Serverless Data Lake & Dashboard

**Short description**
EventBridge -> Lambda ingestion -> S3 raw/transformed -> Glue Crawler -> Athena -> Dashboard.

**Quickstart**
1. Configure \`infra/template.yml\` with \`RAW_BUCKET\`.
2. \`sam build && sam deploy --guided\` (eu-west-1).
3. Run \`scripts/glue_setup.sh\` to create crawler (if required).

**Evidence**
- CloudWatch logs, S3 raw/processed listing, Athena sample query results.
"
      ;;
    4)
      content="# Project ${num} — Radiology DICOM Metadata ETL

**Short description**
Upload DICOM metadata (not pixel data) to S3, Lambda extracts metadata via pydicom layer, stores in DynamoDB and exposes API.

**Quickstart**
1. Build pydicom layer: \`infra/layer_build.sh\`.
2. \`sam build && sam deploy --guided\`.
3. Upload sample metadata to \`s3://<BUCKET>/raw/\`.

**Evidence**
- S3 object listing, CloudWatch extraction logs, DynamoDB items, API responses.
"
      ;;
    5)
      content="# Project ${num} — Containerized ML Inference API

**Short description**
Small trained model deployed as a Lambda container and served via API Gateway.

**Quickstart**
1. Place model in \`model/\`.
2. \`scripts/build-and-push.sh\` to push to ECR.
3. \`scripts/deploy.sh\` to create Lambda + API Gateway.

**Evidence**
- ECR image listed, Lambda config, sample inference curl output.
"
      ;;
    6)
      content="# Project ${num} — AWS FinOps Resource Auditor

**Short description**
Nightly Lambda auditor detects unattached EBS, idle EC2, old snapshots and publishes SNS reports.

**Quickstart**
1. Configure \`infra/template.yml\` role permissions.
2. \`sam build && sam deploy --guided\`.
3. Subscribe to SNS topic to receive reports.

**Evidence**
- SNS report, CloudWatch logs, sample findings CSV.
"
      ;;
    7)
      content="# Project ${num} — Hospital Queue Simulator (SQS + Lambda + DynamoDB)

**Short description**
Producer -> SQS -> Lambda consumer -> DynamoDB occupancy store. Producer can run in CloudShell.

**Quickstart**
1. \`sam build && sam deploy --guided\`.
2. Run \`producer/producer.py\` (CloudShell or local).
3. Monitor DynamoDB and logs.

**Evidence**
- SQS attributes, DynamoDB state dumps, CloudWatch logs.
"
      ;;
    8)
      content="# Project ${num} — Intelligent Invoice Processor (Textract + Lambda + S3)

**Short description**
Upload invoices to S3; Lambda calls Textract and writes structured fields to S3/DynamoDB.

**Quickstart**
1. Configure Textract usage and OUTPUT_BUCKET in \`infra/template.yml\`.
2. \`sam build && sam deploy --guided\`.
3. Upload sample PDFs (keep small to remain in free-tier).

**Evidence**
- Textract responses, output CSV, SNS notifications.
"
      ;;
    *)
      content="# ${proj}\n"
      ;;
  esac

  write_file "${README_PATH}" "${content}"

  # Write a placeholder infra/template.yml per project (do not clobber unless FORCE)
  TPL_PATH="${proj}/infra/template.yml"
  tpl_content="# ${proj} - placeholder infra/template.yml
# Replace placeholders with project-specific resources (Lambda, S3, DynamoDB, SQS, EC2, etc.)
AWSTemplateFormatVersion: '2010-09-09'
Description: \"${proj} infra - replace with real template\"
Resources: {}
"
  write_file "${TPL_PATH}" "${tpl_content}"

  # Create a placeholder script in scripts/ (deploy.sh) if missing
  DEPLOY_SH="${proj}/scripts/deploy.sh"
  deploy_sh_content="#!/usr/bin/env bash
# ${proj}/scripts/deploy.sh - project deploy helper (template)
# Usage: bash scripts/deploy.sh
echo \"This is a placeholder deploy helper for ${proj}. Replace with real deploy commands.\"
echo \"Example: sam build && sam deploy --guided --profile ${DEFAULT_PROFILE} --region ${DEFAULT_REGION}\"
"
  write_file "${DEPLOY_SH}" "${deploy_sh_content}"
  chmod_if_needed "${DEPLOY_SH}"

  # Create a minimal placeholder sample file if empty
  SAMPLE_FILE="${proj}/sample/README.md"
  sample_content="# Sample data for ${proj}
# Add small sample files here for development and testing. Keep files small for Free Tier."
  write_file "${SAMPLE_FILE}" "${sample_content}"

  echo
done

echo "All scaffolds created. Next recommended steps:"
echo "  - review infra/bootstrap/create-deploy-ci.sh and infra/shared-policies/deploy-ci-policy.json, edit and run with admin credentials"
echo "  - edit each project infra/template.yml to include your SAM/CloudFormation resources"
echo "  - run per-project deploy scripts after configuring deploy-ci/profile and packaging bucket"
echo
