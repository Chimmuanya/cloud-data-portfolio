# Cloud + Data + AI Engineering Portfolio

### **8 Real-World Projects Across AWS, Data Engineering, Automation, and Healthcare Analytics**

**Author:** Chimmuanya Mogbo

This monorepo presents **eight fully cloud-ready, AWS-native portfolio projects** designed to demonstrate practical engineering ability across key domains:

- **Cloud Architectures:** Serverless, EC2, and Data Lake patterns.

- **Data Engineering & ETL/ELT:** Building robust data pipelines.

- **Document Automation & Intelligent Extraction:** Leveraging AI for business processes.

- **MLOps & API Deployment:** Operationalizing machine learning models.

- **FinOps & Cloud Governance:** Implementing cost management and resource auditing.

- **Event-Driven Simulation:** Designing asynchronous and distributed systems.

- **Healthcare & Radiology Data Workflows:** Handling specialized, sensitive data formats.

All projects are designed to run on the **AWS Free Tier**, utilize **infrastructure-as-code where applicable**, and include comprehensive **evidence collection** to demonstrate reproducibility and correctness.

---

# Projects Overview (1-8)

Below is a high-level introduction to each project in the portfolio, detailing the technical challenge and solution.

---

## **Project 1 - Serverless Data Quality Pipeline (Completed)**

**Architecture:** S3 → Lambda → QC JSON reports (Serverless ETL)

This is the flagship foundational project of the portfolio, demonstrating a production-grade serverless data pipeline.

**The Production Story: Motivation & Challenges** The 'Why': This project addressed unreliable data ingestion by shifting quality assurance to an immediate, event-driven process. This prevents data lake corruption and provides zero-latency feedback to data owners.

**Key Challenges Solved:**

- **Stream Processing:** Parsed CSVs within Lambda memory limits using streaming, avoiding full-file downloads.

- **Data Integrity:** Enforced primary key uniqueness and strict type coercion (handling strings in integer fields) without external database lookups.

- **Circular Dependencies:** Solved SAM/CloudFormation deployment issues regarding S3 triggers on existing buckets by decoupling the event mapping.

**Technical Stack & Evidence:**

- **Architecture:** Event-driven Lambda (Python 3.10), S3 Event Notifications, IAM Least Privilege.

- **Evidence:** Includes automated logs, QC JSON outputs, and CloudFormation `describe-stack` proofs.

---

## **Project 2 - Public Health Serverless Data Lake & Dashboard**

**Architecture:** EventBridge → Lambda ingestion → S3 Data Lake → Athena → EC2/Streamlit

**Goal:** Weekly ingestion of WHO/CDC public health indicators to build a public health analytics platform.

- **Ingestion:** Lambda triggered by an EventBridge Schedule.

- **Storage:** S3 Data Lake (Partitioned).

- **Query Layer:** AWS Glue Crawler + Athena for SQL-based analysis.

- **Visualization:** Streamlit application hosted on an EC2 t2.micro, secured with Nginx.

**Key Skill:** Connecting serverless data lakes to instance-based compute (EC2) using Instance Profiles for secure data access.

---

## **Project 3 - Radiology DICOM Metadata ETL Pipeline**

**Architecture:** S3 (raw DICOM) → Lambda (pydicom) → DynamoDB → API Gateway

**Goal:** Extract and catalog medical imaging metadata without exposing PHI pixel data.

- **Extraction:** Lambda using a custom `pydicom` layer to parse headers.

- **Storage:** DynamoDB table (`RadiologyMetadata`) for fast, non-relational lookups.

- **API:** API Gateway endpoint (`GET /studies`) to query metadata by modality.

**Key Skill:** Handling unstructured medical data formats (DICOM) in a serverless environment while maintaining PHI-safe practices.

---

## **Project 4 - Containerized ML Inference API (Churn Model)**

**Architecture:** Lambda Container Image → API Gateway → S3 Model Storage

**Goal:** Productionize a machine learning model using Docker and Serverless architecture for scalable inference.

- **Model:** Scikit-learn churn model trained offline, serialized to `.joblib`.

- **Packaging:** Dockerfile based on `public.ecr.aws/lambda/python:3.11`.

- **Deployment:** AWS SAM deploying from ECR (Elastic Container Registry).

**Key Skill:** MLOps fundamentals—moving from a "model in a notebook" to a "model as an API" using containerization.

---

## **Project 5 - AWS FinOps Resource Auditor**

**Architecture:** EventBridge → Lambda (boto3 auditing) → SNS Alerts

**Goal:** Automate cost governance by identifying and reporting on wasted cloud resources.

- **Auditor:** Nightly Lambda using `boto3` to scan for:
  - Idle EC2 instances (< 5% CPU)
  - Unattached EBS volumes
  - Unused Elastic IPs
  - Old Snapshots (> 90 days)

- **Alerting:** Amazon SNS topic for email/SMS notifications to stakeholders.

**Key Skill:** Infrastructure management and FinOps automation via Python SDKs (`boto3`).

---

## **Project 6 - Real-Time Hospital Queue Simulator (SQS + Lambda)**

**Architecture:** Producer → SQS Queue → Lambda Consumer → DynamoDB → S3

**Goal:** Simulate and process real-time patient arrival streams for hospital operations analysis.

- **Producer:** Local/CloudShell script sending synthetic events to SQS.

- **Consumer:** Lambda processing batch events from the queue.

- **State Store:** DynamoDB for tracking current ER occupancy and wait times.

- **Archive:** S3 for historical admission logs.

**Key Skill:** Designing decoupled, asynchronous messaging patterns (SQS) crucial for high-scale, fault-tolerant applications.

---

## **Project 7 - Intelligent Invoice Processor (Textract + Lambda)**

**Architecture:** S3 → Textract → Lambda → S3 Outputs + SNS

**Goal:** Automate data entry from PDF invoices using a managed AI service.

- **AI Service:** Amazon Textract (managed OCR/IDP) to detect Vendor, Total, and Date.

- **Processing:** Lambda parses the Textract JSON response into a structured CSV format.

- **Output:** Appends results to a consolidation file in S3.

**Key Skill:** Integrating Managed AI Services (AIaaS) to solve common business process problems like document processing.

---

## **Project 8 - Business KPI Dashboard on AWS (EC2 + Athena)**

**Architecture:** S3 (data storage) → Athena SQL → Streamlit on EC2

**Goal:** Create a cost-effective Business Intelligence (BI) solution for finance/e-commerce metrics.

- **Data:** Sales metrics stored in S3.

- **Engine:** Athena for running SQL queries directly on raw CSV/Parquet data.

- **Frontend:** Streamlit application querying Athena via `boto3`.

**Key Skill:** Building cost-effective BI platforms using cloud-native, serverless query engines.

---

# Repository Structure

```
cloud-data-ai-portfolio/
│
├── project-01-serverless-data-qc/
├── project-02-kpi-dashboard/
├── project-03-public-health-datalake/
├── project-04-radiology-dicom-etl/
├── project-05-ml-inference-api/
├── project-06-finops-auditor/
├── project-07-hospital-queue-simulator/
└── project-08-invoice-idp/
```

Each project folder is self-contained with:

- `src/`: Application code (Lambda handlers, scripts).

- `infra/`: Infrastructure as Code (SAM templates, CloudFormation).

- `evidence/`: Screenshots, logs, and proof of execution.

- `README.md`: Project-specific setup and runbooks.

---

# Tooling & Workflow

### **Atomic Commit Workflow**

- Follow **Conventional Commits** (`feat:`, `chore:`, `fix:`, `docs:`).

- Use small, traceable, atomic commits per change to demonstrate professional git hygiene.

### **Diagram Workflow**

- Source files stored in `diagrams/*.drawio`.

- Exported artifacts (PNG/SVG) stored in `diagrams/exported/`.

### **Helper Scripts**

Located in `/scripts` or individual project folders:

- `atomic_commit.sh` for standardization.

- `capture-evidence.sh` for automating proof collection.

---

# How to Use This Repo

**1. Browse Each Project** Every project has a full `README.md` with deployment steps, architecture diagrams, and testing instructions.

**2. Deploy Projects Individually** Each project folder contains its own `infra/` folder and `scripts/deploy.sh`. Projects are designed to be deployed independently.

**3. Follow AWS Least-Privilege Practices** All projects use a dedicated `deploy-ci` IAM user (created via bootstrap) to simulate a real-world CI/CD permission boundary, rather than using Root or Admin credentials.

**4. Capture Evidence** Most projects include helper scripts and guidance for capturing evidence, such as CloudWatch log extraction and S3 report collection.

---

# Goals of This Portfolio

This portfolio is designed to demonstrate:

- **Build production-ready, serverless AWS architectures.**

- **Create automated ETL pipelines** for both healthcare and general business domains.

- **Deploy ML models to cloud inference endpoints** (MLOps).

- **Automate cloud governance (FinOps)** using Python SDKs.

- **Use event-driven messaging (SQS/SNS/EventBridge)** for decoupled systems.

- **Perform document AI extraction** with Amazon Textract.

- **Develop BI dashboards** on EC2 and query Athena.

This body of work demonstrates strong cloud engineering ability across industries, with a selective healthcare specialization (radiology + public health) that provides a unique differentiator.

---

# Contact

For portfolio review, collaboration, or cloud work: Chimmuanya Mogbo** @ [Chimmuanyamogbo@gmail.com](mailto:Chimmuanyamogbo@gmail.com), Linkedin: [https://linkedin.com/in/chimmuanya-mogbo](https://linke)

