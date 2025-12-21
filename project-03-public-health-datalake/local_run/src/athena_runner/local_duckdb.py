# src/athena_runner/local_duckdb.py
"""
LOCAL DuckDB analytics runner.
Executes Athena-compatible SQL locally using DuckDB.
This module is invoked ONLY via athena_runner.runner when MODE=LOCAL.
"""
from pathlib import Path
import os
import json
import time
import re
import duckdb
from common.config import (
    MODE,
)
from common.logging import setup_logging

logger = setup_logging(__name__)


sql_dir = Path.cwd() / "local_sql" / "athena" / "queries"
local_clean_dir = Path.cwd() / "local_data" / "clean"
athena_evidence_dir = Path.cwd() / "evidence" / "athena"

# ============================================================================
# OUTPUT FORMAT CONFIGURATION
# ============================================================================
# Control which output formats to generate for query results
# Set via environment variables or modify defaults here
# ============================================================================

EXPORT_JSON = os.getenv("DUCKDB_EXPORT_JSON", "true").lower() == "true"
EXPORT_CSV = os.getenv("DUCKDB_EXPORT_CSV", "true").lower() == "true"

logger.info("Output format configuration:")
logger.info("  - JSON export: %s", EXPORT_JSON)
logger.info("  - CSV export: %s", EXPORT_CSV)

if not EXPORT_JSON and not EXPORT_CSV:
    logger.warning("WARNING: Both JSON and CSV exports are disabled!")

# logger.info("local_clean_dir resolved to: %s", local_clean_dir)
# logger.info("local_clean_dir exists: %s", local_clean_dir.exists())
# logger.info("local_clean_dir is dir: %s", local_clean_dir.is_dir())
# logger.info(
#     "local_clean_dir contents: %s",
#     [p.name for p in local_clean_dir.iterdir()]
# )


def translate_athena_to_duckdb(sql: str) -> str:
    """
    Translate Athena (Presto/Trino) SQL syntax to DuckDB-compatible SQL.

    Args:
        sql: Original Athena SQL query

    Returns:
        DuckDB-compatible SQL query
    """
    original_sql = sql

    # 1. Convert date_add() to INTERVAL syntax
    # Pattern: date_add('unit', value, date)
    # Examples:
    #   date_add('year', -3, CURRENT_DATE) -> CURRENT_DATE - INTERVAL '3 years'
    #   date_add('day', 30, some_date) -> some_date + INTERVAL '30 days'

    def replace_date_add(match):
        unit = match.group(1).lower()
        value = match.group(2).strip()
        date_expr = match.group(3).strip()

        # Handle negative values
        if value.startswith('-'):
            operator = '-'
            value = value[1:]
        else:
            operator = '+'

        # Map Athena units to DuckDB units (add plural 's')
        unit_map = {
            'year': 'years',
            'month': 'months',
            'day': 'days',
            'hour': 'hours',
            'minute': 'minutes',
            'second': 'seconds',
        }
        duckdb_unit = unit_map.get(unit, unit + 's')

        return f"{date_expr} {operator} INTERVAL '{value}' {duckdb_unit}"

    sql = re.sub(
        r"date_add\s*\(\s*['\"](\w+)['\"]\s*,\s*([+-]?\d+)\s*,\s*([^)]+)\)",
        replace_date_add,
        sql,
        flags=re.IGNORECASE
    )

    # 2. Convert date_diff() to DuckDB's date_diff()
    # Athena: date_diff('unit', start, end)
    # DuckDB: date_diff('unit', start, end) - SAME! But let's normalize
    # Note: DuckDB's date_diff has start and end in same order

    # 3. Convert CURRENT_TIMESTAMP for consistency
    sql = re.sub(
        r'\bCURRENT_TIMESTAMP\b',
        'current_timestamp',
        sql,
        flags=re.IGNORECASE
    )

    # 4. Convert CURRENT_DATE for consistency
    sql = re.sub(
        r'\bCURRENT_DATE\b',
        'current_date',
        sql,
        flags=re.IGNORECASE
    )

    # 5. Convert array literals: array[1,2,3] -> [1,2,3]
    sql = re.sub(
        r'\barray\s*\[',
        '[',
        sql,
        flags=re.IGNORECASE
    )

    # 6. Convert sequence() to generate_series()
    # Athena: sequence(start, stop, step)
    # DuckDB: generate_series(start, stop, step)
    sql = re.sub(
        r'\bsequence\s*\(',
        'generate_series(',
        sql,
        flags=re.IGNORECASE
    )

    # 7. Convert arbitrary() to any_value()
    # Athena: arbitrary(column)
    # DuckDB: any_value(column)
    sql = re.sub(
        r'\barbitrary\s*\(',
        'any_value(',
        sql,
        flags=re.IGNORECASE
    )

    # 8. Convert cardinality() to array_length() or list_length()
    # Athena: cardinality(array_column)
    # DuckDB: len(array_column) or array_length(array_column)
    sql = re.sub(
        r'\bcardinality\s*\(',
        'len(',
        sql,
        flags=re.IGNORECASE
    )

    # 9. Convert from_unixtime() to to_timestamp()
    # Athena: from_unixtime(epoch)
    # DuckDB: to_timestamp(epoch)
    sql = re.sub(
        r'\bfrom_unixtime\s*\(',
        'to_timestamp(',
        sql,
        flags=re.IGNORECASE
    )

    # 10. Convert approx_distinct() to approx_count_distinct()
    sql = re.sub(
        r'\bapprox_distinct\s*\(',
        'approx_count_distinct(',
        sql,
        flags=re.IGNORECASE
    )

    # Log translation if changes were made
    if sql != original_sql:
        logger.debug("SQL translated from Athena to DuckDB syntax")
        logger.debug("Original: %s", original_sql[:200])
        logger.debug("Translated: %s", sql[:200])

    return sql


def run_duckdb_queries():
    if MODE != "LOCAL":
        raise RuntimeError("run_duckdb_queries() called outside LOCAL mode")

    logger.info("Running DuckDB analytics locally")

    # SQL files are at project-root/local_run/local_sql/athena/queries/
    # sql_dir = PROJECT_ROOT / "local_run" / "local_sql" / "athena" / "queries"

    logger.info("SQL directory: %s", sql_dir)

    if not sql_dir.exists():
        raise RuntimeError(f"SQL directory not found: {sql_dir}")

    sql_files = list(sql_dir.glob("*.sql"))
    if not sql_files:
        raise RuntimeError(f"No .sql files found in: {sql_dir}")

    logger.info("Found %d SQL files", len(sql_files))

    athena_evidence_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(database=":memory:")
    con.execute("CREATE SCHEMA IF NOT EXISTS project03_db")

    registered = []

    for dataset_dir in local_clean_dir.iterdir():
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

        # Read original SQL
        athena_sql = sql_file.read_text(encoding="utf-8").strip()

        # Translate to DuckDB syntax
        duckdb_sql = translate_athena_to_duckdb(athena_sql)

        # Execute translated query
        start = time.perf_counter()

        try:
            df = con.execute(duckdb_sql).fetchdf()
        except Exception as e:
            logger.error("Query failed: %s", sql_file.name)
            logger.error("Original SQL: %s", athena_sql[:500])
            logger.error("Translated SQL: %s", duckdb_sql[:500])
            logger.error("Error: %s", e)
            raise

        duration_ms = int((time.perf_counter() - start) * 1000)

        # ============================================================================
        # EXPORT RESULTS IN CONFIGURED FORMATS
        # ============================================================================
        output_files = []

        # Export to JSON
        if EXPORT_JSON:
            json_path = athena_evidence_dir / f"{sql_file.stem}.json"
            df.to_json(
                json_path,
                orient="records",
                date_format="iso",  # Converts datetime/timestamp to ISO 8601 strings
                indent=2
            )
            output_files.append(str(json_path))
            logger.debug("  ✓ Exported JSON: %s", json_path.name)

        # Export to CSV
        if EXPORT_CSV:
            csv_path = athena_evidence_dir / f"{sql_file.stem}.csv"
            df.to_csv(
                csv_path,
                index=False,
                date_format="%Y-%m-%d %H:%M:%S"  # Format datetime columns
            )
            output_files.append(str(csv_path))
            logger.debug("  ✓ Exported CSV: %s", csv_path.name)

        query_metrics.append({
            "query": sql_file.stem,
            "rows": len(df),
            "duration_ms": duration_ms,
            "outputs": output_files,  # Changed from 'output' to 'outputs' (list)
            "formats": {
                "json": EXPORT_JSON,
                "csv": EXPORT_CSV,
            },
            "translated": athena_sql != duckdb_sql,
        })

        logger.info(
            "Query %s → %d rows (%d ms)",
            sql_file.stem,
            len(df),
            duration_ms,
        )

    metrics_path = athena_evidence_dir / "_query_metrics.json"
    metrics_path.write_text(
        json.dumps(query_metrics, indent=2),
        encoding="utf-8",
    )

    logger.info("DuckDB analytics complete: %d queries executed", len(query_metrics))
