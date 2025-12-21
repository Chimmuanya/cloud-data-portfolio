# Project 03: Local Development Workflow

This project implements a local development environment designed to simulate the public health data lake pipeline without AWS dependencies. It provides a sandbox for rapid iteration, debugging, and analytics validation using a hybrid execution model.

## Overview

The workflow allows developers to run the full data pipeline—from ingestion to dashboard generation—on a local machine. By setting the environment variable `MODE=LOCAL`, the system swaps AWS services (S3, Athena) for local alternatives (Filesystem, DuckDB) while using the same core application logic found in `src/`.

## Directory Structure

The `local_run/` directory orchestrates the local environment:

* **local_data/**: Contains local storage for raw (JSON) and clean (Parquet/CSV) data.
* **local_sql/**: Houses DuckDB logic and SQL queries compatible with Athena.
* **evidence/**: Stores local analytics outputs and dashboard assets.
* **.venv/**: Local Python virtual environment (git-ignored).
* **requirements.local.txt**: Dependencies specific to the local simulation.
* **Makefile**: Automation script for environment setup and execution.

## Key Design Principles

1. **Cloud Independence**: No AWS SDK calls, IAM roles, or S3 buckets are required.
2. **Code Parity**: The logic in `src/` is shared across environments. The execution path is toggled via the `MODE` environment variable.
3. **Unified Analytics Control**: The `athena_runner` utility manages execution. In `LOCAL` mode, it targets DuckDB; in `CLOUD` mode, it targets AWS Athena.

## Getting Started

### Prerequisites

* Python 3.11
* Make (optional, but recommended)

### Automated Execution (Recommended)

The included Makefile automates environment creation and pipeline execution. Run the following command from the repository root:

```bash
make local-run
```

This command performs the following steps:

1. Creates a virtual environment in `local_run/.venv`.
2. Installs dependencies from `requirements.local.txt`.
3. Executes the full simulation: Ingestion, Transformation, Analytics (DuckDB), and Dashboard build.

### Manual Execution

For granular control, you can run the components manually:

```bash
# Activate the environment
source local_run/.venv/bin/activate

# Set environment variables
export MODE=LOCAL
export PYTHONPATH=$(pwd)/src

# Run the simulation script
bash scripts/run_local_simulation.sh
```

## Available Make Targets

* `make venv`: Initialize the local virtual environment.
* `make deps`: Upgrade pip and install local requirements.
* `make local-run`: Execute the end-to-end local simulation.
* `make clean`: Remove the local virtual environment and build artifacts.

## Expected Outputs

Upon a successful run, the following artifacts are generated:

* **Raw Data**: JSON files located in `local_run/local_data/raw/`.
* **Clean Data**: Parquet and CSV files in `local_run/local_data/clean/`.
* **Analytics**: Query results stored in `local_run/evidence/athena/`.
* **Dashboard**: Locally renderable HTML or static assets for previewing visualizations.

## Development Standards

* Do not commit the `.venv/` directory.
* Avoid hardcoded paths: Utilize `common.config` as the single source of truth for path resolution.
* Shell Scripts: Use scripts only for orchestration; maintain all business logic within Python modules.
