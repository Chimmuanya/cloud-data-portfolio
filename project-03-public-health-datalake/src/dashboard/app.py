import os
import boto3  # Move to top
from build import build_dashboard
from common.logging import setup_logging

logger = setup_logging(__name__)
s3 = boto3.client("s3") # Initialize once per execution environment

def lambda_handler(event, context):
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
