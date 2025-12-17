# src/athena_runner/app.py

from runner import run_all
from common.logging import setup_logging

logger = setup_logging(__name__)

def lambda_handler(event, context):
    """
    Lambda entry point.
    Runs Athena DDLs and analytical queries, writes CSVs to Evidence bucket.
    """

    logger.info("Athena runner Lambda invoked")

    result = run_all()

    return {
        "status": "ok",
        "queries_executed": result["queries"],
        "ddls_executed": result["ddls"],
    }
