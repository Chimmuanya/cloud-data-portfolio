import os
import json
import boto3
from build import build_dashboard
from common.logging import setup_logging

logger = setup_logging(__name__)
s3 = boto3.client("s3")

def lambda_handler(event, context):
    try:
        # --- 1. DEFENSIVE PARSING ---
        # Check if this is a standard SNS event
        if 'Records' in event and 'Sns' in event['Records'][0]:
            sns_body = event['Records'][0]['Sns']['Message']
            sns_message = json.loads(sns_body)

            # Extract S3 details from the inner message
            s3_event = sns_message['Records'][0]['s3']
            bucket = s3_event['bucket']['name']
            key = s3_event['object']['key']
            logger.info(f"Triggered by SNS for file: s3://{bucket}/{key}")

        # Optional: Handle direct S3 triggers (useful for manual testing)
        elif 'Records' in event and 's3' in event['Records'][0]:
            bucket = event['Records'][0]['s3']['bucket']['name']
            key = event['Records'][0]['s3']['object']['key']
            logger.info(f"Triggered by direct S3 event: s3://{bucket}/{key}")

        else:
            # If the event structure is totally unexpected
            logger.warning(f"Unexpected event structure: {json.dumps(event)}")
            bucket = "unknown"
            key = "unknown"

        # --- 2. EXECUTION ---
        output_bucket = os.environ.get("EVIDENCE_BUCKET")
        output_key = "dashboard.html"

        logger.info("Generating dashboard HTML via build_dashboard...")
        # Note: Ensure build_dashboard uses the bucket/key if it needs to query specific data
        html = build_dashboard()

        logger.info(f"Uploading dashboard to s3://{output_bucket}/{output_key}")
        s3.put_object(
            Bucket=output_bucket,
            Key=output_key,
            Body=html,
            ContentType="text/html"
        )

        return {
            "status": "ok",
            "output": f"s3://{output_bucket}/{output_key}",
            "triggered_by": f"s3://{bucket}/{key}"
        }

    except Exception as e:
        logger.error(f"Error processing dashboard: {str(e)}")
        # Re-raising allows Lambda to mark the invocation as failed
        raise e
