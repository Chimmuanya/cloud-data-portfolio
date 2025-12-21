#!/usr/bin/env python3
"""
scripts/athena/run_queries_local.py

LOCAL analytics runner using DuckDB.

- Mirrors Athena table layout
- Discovers datasets automatically from local_run/local_data/clean/
- Executes SQL templates from local_run/local_sql/duckdb/queries/
- Writes query results to local_run/evidence/athena/

LOCAL-ONLY. No AWS dependencies.
"""

from pathlib import Path
import duckdb
import json
import sys
import time


from common.config import (
    LOCAL_CLEAN_DIR,
    PROJECT_ROOT,
    ATHENA_EVIDENCE_DIR,
)
from common.logging import setup_logging

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logger = setup_logging(__name__)
logger.info("Running DuckDB local analytics")

# ------------------------------------------------------------------
# Sanity checks
# ------------------------------------------------------------------
assert PROJECT_ROOT.exists(), f"PROJECT_ROOT invalid: {PROJECT_ROOT}"

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
SQL_DIR = PROJECT_ROOT / "local_run" / "local_sql" / "duckdb" / "queries"
ATHENA_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# DuckDB connection (explicit in-memory)
# ------------------------------------------------------------------
con = duckdb.connect(database=":memory:")

# ------------------------------------------------------------------
# Create Athena-mirroring schema
# ------------------------------------------------------------------

query_metrics = []


con.execute("CREATE SCHEMA IF NOT EXISTS project03_db")

# ------------------------------------------------------------------
# Register Parquet datasets as DuckDB views
# ------------------------------------------------------------------
logger.info("Registering Parquet datasets")

if not LOCAL_CLEAN_DIR.exists():
    logger.error("LOCAL_CLEAN_DIR does not exist: %s", LOCAL_CLEAN_DIR)
    sys.exit(1)

registered = []

for endpoint_dir in LOCAL_CLEAN_DIR.iterdir():
    if not endpoint_dir.is_dir():
        continue

    endpoint = endpoint_dir.name
    parquet_glob = str(endpoint_dir / "year=*/data.parquet")

    logger.info("Using parquet glob: %s", parquet_glob)

    try:
        con.execute(f"""
            CREATE OR REPLACE VIEW project03_db."{endpoint}" AS
            SELECT * FROM read_parquet('{parquet_glob}')
        """)
        registered.append(endpoint)
        logger.info("Registered dataset: project03_db.%s", endpoint)
    except Exception as exc:
        logger.warning("Skipped %s (no parquet?): %s", endpoint, exc)

if not registered:
    logger.error("No datasets registered — aborting SQL execution")
    sys.exit(1)

# ------------------------------------------------------------------
# Execute SQL templates
# ------------------------------------------------------------------
logger.info("Executing SQL templates")

if not SQL_DIR.exists():
    logger.warning("No SQL directory found: %s", SQL_DIR)
    sys.exit(0)

for sql_file in sorted(SQL_DIR.glob("*.sql")):
    logger.info("Running query: %s", sql_file.name)

    sql = sql_file.read_text(encoding="utf-8").strip()

    start = time.perf_counter()
    try:
        df = con.execute(sql).fetchdf()
    except Exception as exc:
        logger.error("Query failed: %s → %s", sql_file.name, exc)
        continue
    duration_ms = int((time.perf_counter() - start) * 1000)

    out_path = ATHENA_EVIDENCE_DIR / f"{sql_file.stem}.json"
    out_path.write_text(
        json.dumps(df.to_dict(orient="records"), indent=2),
        encoding="utf-8"
    )

    metric = {
        "query": sql_file.stem,
        "rows": len(df),
        "duration_ms": duration_ms,
        "output": str(out_path),
    }
    query_metrics.append(metric)

    logger.info(
        "Query %s → %d rows (%d ms)",
        sql_file.name,
        len(df),
        duration_ms,
    )

logger.info("DuckDB local analytics complete")

metrics_path = ATHENA_EVIDENCE_DIR / "_query_metrics.json"
metrics_path.write_text(
    json.dumps(query_metrics, indent=2),
    encoding="utf-8"
)

logger.info("Query metrics written → %s", metrics_path)

