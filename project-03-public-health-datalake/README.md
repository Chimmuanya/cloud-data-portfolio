# Project 03 – Public Health Data Lake

## Overview

This project implements a **cloud-ready public health data lake** designed to ingest, normalize, query, and visualize global health indicators (WHO, World Bank, outbreak events). It is intentionally structured to be:

* **Reproducible** (Infrastructure as Code)
* **Environment-agnostic** (local ↔ cloud parity)
* **Auditable** (append-only evidence, generated artifacts isolated)
* **Beginner-safe but industry-aligned**

The repository separates **authoritative source artifacts** from **generated outputs**, and **local logic** from **cloud execution**, mirroring real-world data engineering practice.

---

## High-Level Architecture

**Flow (Conceptual):**

1. **Ingest** – Fetch raw public health data (APIs / files)
2. **ETL** – Normalize and harmonize datasets into analytics-ready form
3. **Storage** – Raw and clean data stored in S3 (cloud) or local equivalents
4. **Query** – SQL templates materialized for Athena (or DuckDB locally)
5. **Dashboard** – Charts and indicators built from query outputs
6. **Evidence** – Logs, query results, and screenshots captured for audit

The same Python and SQL logic is used locally and in AWS.

---

## Repository Structure (Why It Looks Like This)

```
project-03-public-health-datalake/
├── cloud/        # Everything AWS / IaC
├── src/          # Pure Python (local == cloud)
├── sql/          # Engine-agnostic SQL logic
├── scripts/      # CLI entry points
├── evidence/     # Append-only outputs
├── notebooks/    # Scratch / exploration only
```

### Key Design Rules

* **Templates are never executed directly**
* **Generated files are never edited manually**
* **Evidence is append-only**
* **src/** must remain cloud-agnostic

---

## Cloud Directory (`cloud/`)

### `cloud/templates/`

Authoritative Infrastructure-as-Code templates.

* `template.yml` – SAM / CloudFormation template using `${ENV_VARS}`
* `policies/` – IAM policies (deployment, buckets, least privilege)
* `athena/` – Canonical DDLs for analytics tables

These files are **human-edited** and version-controlled.

---

### `cloud/generated/`

Auto-generated artifacts created by substitution scripts.

* Environment variables are injected
* Files are safe to deploy
* **Never edit manually**

This directory is typically `.gitignore`d.

---

### `cloud/scripts/`

Cloud-side orchestration scripts:

* `envsubst.sh` – Single canonical variable substitution wrapper
* `bootstrap.sh` – Creates buckets, IAM roles, base resources
* `deploy.sh` – `sam build` + `sam deploy`
* `run_pipeline.sh` – Triggers ingest → etl → queries

These scripts define **how cloud resources are created and used**.

---

## Source Code (`src/`)

Pure Python. No AWS-specific imports unless strictly required.

### `src/ingest/`

Responsible for acquiring raw public health data.

* API calls
* File downloads
* Schema-light storage

### `src/etl/`

Responsible for **data normalization and harmonization**.

* Column standardization
* Type coercion
* Missing value handling
* Partition-aware outputs

### `src/dashboard/`

Responsible for **analytics and visualization logic**.

* Query loading
* Transformations
* Chart generation

### `src/common/`

Shared utilities:

* `config.py` – Environment variable handling
* `logging.py` – Consistent logging setup

---

## SQL (`sql/`)

SQL is treated as **first-class logic**, not embedded strings.

### `sql/templates/`

* Parameterized SQL with `${VARS}`
* Engine-agnostic where possible

### `sql/generated/`

* Substituted SQL ready for execution
* Used by Athena or DuckDB
* Never edited manually

---

## Scripts (`scripts/`)

CLI entry points that glue everything together.

* `run_local.sh` – One-command local pipeline
* `queries.sh` – Execute SQL against Athena or DuckDB
* `capture_evidence.sh` – Collect logs, query outputs, screenshots
* `requirements.txt` – Python dependencies

These scripts are intentionally thin and explicit.

---

## Evidence (`evidence/`)

Append-only artifacts proving the system worked.

* `athena/` – Query results
* `dashboard/` – Charts, screenshots
* `logs/` – Execution logs

Nothing here is overwritten or cleaned automatically.

---

## Notebooks (`notebooks/`)

Optional and **non-production**.

Used for:

* Exploration
* Debugging
* Prototyping

No notebook should be required to run the pipeline.

---

## Environment Setup

### 1. Prerequisites

Local machine:

* Python 3.10+
* Bash shell
* AWS CLI (for cloud runs)
* SAM CLI (for deployment)

---

### 2. Environment Variables

Copy and edit:

```bash
cp .env.example .env
```

Typical variables:

* `AWS_REGION`
* `ACCOUNT_ID`
* `RAW_BUCKET`
* `CLEAN_BUCKET`
* `ATHENA_RESULTS_BUCKET`

These are consumed by both Python and shell scripts.

---

### 3. Python Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
```

---

## Running Locally

```bash
./scripts/run_local.sh
```

This typically performs:

1. Ingest (local)
2. ETL (local)
3. SQL generation
4. Local query execution (DuckDB)

Outputs are written to `evidence/`.

---

## Running in AWS

### 1. Bootstrap (once)

```bash
cd cloud/scripts
./bootstrap.sh
```

Creates:

* S3 buckets
* IAM roles
* Base permissions

---

### 2. Deploy

```bash
./deploy.sh
```

* Substitutes templates
* Builds SAM application
* Deploys CloudFormation stack

---

### 3. Run Pipeline

```bash
./run_pipeline.sh
```

Triggers the full cloud workflow.

---

## Generated vs Authoritative Files (Important)

| Type         | Editable      | Versioned  |
| ------------ | ------------- | ---------- |
| `templates/` | Yes           |  Yes       |
| `generated/` | No            |  Optional  |
| `evidence/`  | Append-only   |  No        |

This separation prevents accidental drift and deployment errors.

---

## Status

* **Learning-focused but production-aligned**
* **Actively evolving**
* Some automation may still be refined

---

## Notes

This project is intentionally designed to demonstrate:

* Practical data engineering structure
* Infrastructure discipline No          | ❌ Optional |
| `evidence/`  | ❌ Appen
* Clear separation of concerns
* Reproducible analytics pipelines

Feedback, issues, and suggestions are welcome.
