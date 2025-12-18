# src/athena_runner/app.py

from runner import run_all
from common.logging import setup_logging

logger = setup_logging(__name__)

def lambda_handler(event, context):
    """
    Lambda entry point.
    Runs Athena DDLs and analytical queries, writes CSVs to Evidence bucket.
    """

    # 1. Unwrap the SNS layer
    sns_message = json.loads(event['Records'][0]['Sns']['Message'])

    # 2. Access the standard S3 event data
    s3_event = sns_message['Records'][0]['s3']
    bucket = s3_event['bucket']['name']
    key = s3_event['object']['key']

    logger.info(f"Athena runner triggered by SNS for file: s3://{bucket}/{key}")

#    logger.info("Athena runner Lambda invoked")

    result = run_all()

    return {
        "status": "ok",
        "queries_executed": result["queries"],
        "ddls_executed": result["ddls"],
    }
