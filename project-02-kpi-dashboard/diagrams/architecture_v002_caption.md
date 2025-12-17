### Architecture v001

**Primary Flow:** The GitHub repository (ETL + dashboard) is cloned or deployed to the EC2 instance. The ETL outputs (`data/processed/*`) are uploaded to an S3 bucket (`project02-kpi-ecommerce`) either manually, by CI (GitHub Actions), or by running `python -m src.preprocess`. The EC2-hosted Streamlit app (systemd service) reads those CSV/Parquet artifacts directly from S3 (using the instance IAM role `EC2_Project02_S3ReadOnly`) and serves the dashboard to end users at `http://<public-ip>:8501`. CloudWatch collects logs and basic metrics from the EC2 instance and the app.

**Key Components**

* **GitHub repo** — source for `preprocess.py`, `src/dashboard/app.py`, CI workflows.
* **EC2 (t2.micro)** — Ubuntu, Python venv, runs Streamlit on port 8501, managed by `systemd`.
* **S3 bucket** (`project02-kpi-ecommerce`) — stores processed artifacts under `processed/` (daily_kpis, top_products, rfm, sample_kpis, metadata.json).
* **IAM Role** (`EC2_Project02_S3ReadOnly`) — attached to EC2 to allow `s3:GetObject` and read-only access to the processed prefix.
* **Security Group** (`project02-streamlit-sg`) — allows SSH from admin IP and HTTP (8501) from allowed sources.
* **VPC / IGW / Public Subnet** — network placement for the EC2 instance; Internet Gateway routes external traffic to the instance.
* **CloudWatch** — forwards Streamlit and system logs, provides EC2 metrics for monitoring.

**Data flow (step-by-step)**

1. Developer commits code to GitHub (ETL + dashboard).
2. ETL run produces `data/processed/*` (locally or in CI).
3. `data/processed/*` uploaded to `s3://project02-kpi-ecommerce/processed/` (manual or GitHub Actions).
4. EC2 (Streamlit app) reads processed files from S3 using the attached IAM role and renders dashboard views.
5. End users access the app via `http://<ec2-public-ip>:8501`; responses served over Streamlit’s HTTP server.
6. Logs and metrics from the EC2 instance and app are shipped to CloudWatch for troubleshooting and uptime checks.

**Security & Ops notes**

* S3 block public access: **ON**; access limited via IAM role and bucket prefix permissions.
* Security Group should restrict port 8501 to trusted IPs where possible (or sit behind a reverse proxy).
* Optionally configure a VPC S3 Gateway Endpoint to avoid public internet egress for S3 reads.
* Use CloudWatch logs / instance status checks and an external uptime check (or CI artifact `uptime.md`) for simple availability monitoring.

**Status**

* **Created:** 2025-12-09
