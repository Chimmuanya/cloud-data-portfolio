# src/athena_runner/app.py

import json
import boto3
from runner import run_all
from common.logging import setup_logging

logger = setup_logging(__name__)

def lambda_handler(event, context):
    """
    Lambda entry point.
    Runs Athena DDLs and analytical queries, writes CSVs to Evidence bucket.
    """
    try:
        # --- 1. DEFENSIVE PARSING (Same as Dashboard) ---
        if 'Records' in event and 'Sns' in event['Records'][0]:
            # Unwrap the SNS layer
            sns_body = event['Records'][0]['Sns']['Message']
            sns_message = json.loads(sns_body)

            # Access the standard S3 event data from inside SNS
            s3_event = sns_message['Records'][0]['s3']
            bucket = s3_event['bucket']['name']
            key = s3_event['object']['key']
            logger.info(f"Athena runner triggered by SNS for file: s3://{bucket}/{key}")

        elif 'Records' in event and 's3' in event['Records'][0]:
            # Handle direct S3 trigger for manual testing
            bucket = event['Records'][0]['s3']['bucket']['name']
            key = event['Records'][0]['s3']['object']['key']
            logger.info(f"Athena runner triggered by direct S3 event: s3://{bucket}/{key}")

        else:
            logger.warning(f"Athena runner invoked with unexpected event structure. Proceeding with run_all().")
            bucket = "unknown"
            key = "unknown"

        # --- 2. EXECUTION ---
        # run_all() typically handles its own environment variables for
        # ATHENA_DATABASE and ATHENA_OUTPUT_BUCKET
        result = run_all()

        return {
            "status": "ok",
            "queries_executed": result.get("queries", 0),
            "ddls_executed": result.get("ddls", 0),
            "triggered_by": f"s3://{bucket}/{key}"
        }

    except Exception as e:
        logger.error(f"Error in Athena Runner: {str(e)}")
        # Raise allows Lambda to report a failure and trigger retries if configured
        raise e
