#!/usr/bin/env python3
"""
scripts/athena/run_queries_local.py

LOCAL analytics runner using DuckDB.

- Mirrors Athena table layout
- Discovers datasets automatically from data/clean/
- Executes SQL templates from local_sql/
- Writes query results to evidence/athena/

This script is LOCAL-ONLY and has no AWS dependencies.
"""

from pathlib import Path
import duckdb
import json
import sys

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
# Paths
# ------------------------------------------------------------------
SQL_DIR = PROJECT_ROOT / "local_sql"
ATHENA_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# DuckDB connection
# ------------------------------------------------------------------
con = duckdb.connect()

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

    try:
        con.execute(f"""
            CREATE OR REPLACE VIEW {endpoint} AS
            SELECT * FROM read_parquet('{parquet_glob}')
        """)
        registered.append(endpoint)
        logger.info("Registered dataset: %s", endpoint)
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

    sql = sql_file.read_text()

    try:
        df = con.execute(sql).fetchdf()
    except Exception as exc:
        logger.error("Query failed: %s → %s", sql_file.name, exc)
        continue

    out_path = ATHENA_EVIDENCE_DIR / f"{sql_file.stem}.json"
    out_path.write_text(
        json.dumps(df.to_dict(orient="records"), indent=2)
    )

    logger.info(
        "Query %s produced %d rows → %s",
        sql_file.name,
        len(df),
        out_path,
    )

logger.info("DuckDB local analytics complete")
