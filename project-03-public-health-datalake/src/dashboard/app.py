import os
import boto3  # Move to top
from build import build_dashboard
from common.logging import setup_logging

logger = setup_logging(__name__)
s3 = boto3.client("s3") # Initialize once per execution environment

def lambda_handler(event, context):

    # 1. Unwrap the SNS layer
    sns_message = json.loads(event['Records'][0]['Sns']['Message'])

    # 2. Access the standard S3 event data
    s3_event = sns_message['Records'][0]['s3']
    bucket = s3_event['bucket']['name']
    key = s3_event['object']['key']

    logger.info(f"Triggered by SNS for file: s3://{bucket}/{key}")

    output_bucket = os.environ["DASHBOARD_BUCKET"]
    output_key = "dashboard.html"

    logger.info("Generating dashboard HTML in-memory...")
    # Ensure build_dashboard doesn't write to root!
    html = build_dashboard(return_html=True)

    logger.info(f"Uploading dashboard to s3://{output_bucket}/{output_key}")
    s3.put_object(
        Bucket=output_bucket,
        Key=output_key,
        Body=html,
        ContentType="text/html"
    )

    return {
        "status": "ok",
        "output": f"s3://{output_bucket}/{output_key}"
    }
