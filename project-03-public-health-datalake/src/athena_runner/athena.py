# src/athena_runner/athena.py

import time
import boto3
from typing import Optional
from common.config import (
    ATHENA_DATABASE,
    ATHENA_OUTPUT_BUCKET,
    ATHENA_OUTPUT_PREFIX,
    ATHENA_OUTPUT_PATH,
    CLEAN_BUCKET,
)
# from common.config import ATHENA_OUTPUT_PATH
from common.logging import setup_logging

logger = setup_logging(__name__)

# Initialize client globally for connection reuse
athena = boto3.client("athena")


def run_athena_query(
    *,
    sql: str,
    output_prefix: str,
    database: Optional[str] = None,
    poll_seconds: int = 2,
    max_retries: int = 60,  # Increased to 120s total – Athena queries can take >60s
    work_group: str = "primary",  # Make configurable instead of hard-coded
) -> str:
    """
    Run an Athena query and wait for completion.

    Output CSV is written to:
    s3://<ATHENA_OUTPUT_BUCKET>/<ATHENA_OUTPUT_PREFIX>/<output_prefix>/

    Args:
        sql: Query to execute
        output_prefix: Folder prefix inside the Athena output location
        database: Athena database (defaults to ATHENA_DATABASE)
        poll_seconds: Seconds to wait between status checks
        max_retries: Maximum poll attempts before timing out
        work_group: Athena workgroup (usually 'primary')

    Returns:
        QueryExecutionId

    Raises:
        RuntimeError: If query fails or is cancelled
        TimeoutError: If query does not complete within max_retries
    """
    db = database or ATHENA_DATABASE
    # output_location = (
    #     f"s3://{ATHENA_OUTPUT_BUCKET}/"
    #     f"{ATHENA_OUTPUT_PREFIX.rstrip('/')}/{output_prefix.strip('/')}/"
    # )

    logger.info("Submitting Athena query to DB: %s", db)
    # Replace the template placeholder with the actual bucket name from config.py
    prepared_sql = sql.replace("<CLEAN_BUCKET>", CLEAN_BUCKET)

    # Use prepared_sql in the execution call
    response = athena.start_query_execution(
        QueryString=prepared_sql,
        QueryExecutionContext={"Database": db},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT_PATH},
        WorkGroup=work_group
    )

    qid = response["QueryExecutionId"]
    retries = 0

    # --- Poll until finished (with safety exit) ---
    while retries < max_retries:
        execution = athena.get_query_execution(QueryExecutionId=qid)
        status = execution["QueryExecution"]["Status"]["State"]

        if status == "SUCCEEDED":
            logger.info("Athena query SUCCEEDED: %s", qid)
            return qid

        if status in ("FAILED", "CANCELLED"):
            reason = execution["QueryExecution"]["Status"].get("StateChangeReason")
            raise RuntimeError(f"Athena query failed ({status}): {reason}")

        # Still running or queued
        retries += 1
        time.sleep(poll_seconds)

    # If we hit the max_retries limit
    raise TimeoutError(f"Athena query {qid} timed out after {max_retries * poll_seconds}s")

