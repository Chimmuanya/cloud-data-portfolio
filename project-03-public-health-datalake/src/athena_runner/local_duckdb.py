# src/athena_runner/local_duckdb.py

"""
LOCAL DuckDB analytics runner.

Executes Athena-compatible SQL locally using DuckDB.
This module is invoked ONLY via athena_runner.runner when MODE=LOCAL.
"""

from pathlib import Path
import json
import time
import duckdb

from common.config import (
    MODE,
    PROJECT_ROOT,
    LOCAL_CLEAN_DIR,
    ATHENA_EVIDENCE_DIR,
)
from common.logging import setup_logging

logger = setup_logging(__name__)


def run_duckdb_queries():
    if MODE != "LOCAL":
        raise RuntimeError("run_duckdb_queries() called outside LOCAL mode")

    logger.info("Running DuckDB analytics locally")

    sql_dir = (
        PROJECT_ROOT
        / "local_run"
        / "local_sql"
        / "duckdb"
        / "queries"
    )

    ATHENA_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(database=":memory:")
    con.execute("CREATE SCHEMA IF NOT EXISTS project03_db")

    registered = []

    for dataset_dir in LOCAL_CLEAN_DIR.iterdir():
        if not dataset_dir.is_dir():
            continue

        name = dataset_dir.name
        parquet_glob = str(dataset_dir / "year=*/data.parquet")

        logger.info("Registering dataset: %s", name)

        con.execute(f"""
            CREATE OR REPLACE VIEW project03_db."{name}" AS
            SELECT * FROM read_parquet('{parquet_glob}')
        """)

        registered.append(name)

    if not registered:
        raise RuntimeError("No datasets registered for DuckDB")

    logger.info("Registered datasets: %s", ", ".join(registered))

    query_metrics = []

    for sql_file in sorted(sql_dir.glob("*.sql")):
        logger.info("Executing query: %s", sql_file.name)

        sql = sql_file.read_text(encoding="utf-8").strip()

        start = time.perf_counter()
        df = con.execute(sql).fetchdf()
        duration_ms = int((time.perf_counter() - start) * 1000)

        out_path = ATHENA_EVIDENCE_DIR / f"{sql_file.stem}.json"
        out_path.write_text(
            json.dumps(df.to_dict(orient="records"), indent=2),
            encoding="utf-8",
        )

        query_metrics.append({
            "query": sql_file.stem,
            "rows": len(df),
            "duration_ms": duration_ms,
            "output": str(out_path),
        })

        logger.info(
            "Query %s → %d rows (%d ms)",
            sql_file.stem,
            len(df),
            duration_ms,
        )

    metrics_path = ATHENA_EVIDENCE_DIR / "_query_metrics.json"
    metrics_path.write_text(
        json.dumps(query_metrics, indent=2),
        encoding="utf-8",
    )

    logger.info("DuckDB analytics complete")
