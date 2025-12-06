# Project 07 — Hospital Queue Simulator (SQS + Lambda + DynamoDB)

**Short description**
Producer publishes synthetic patient-arrival events to SQS (can run from CloudShell). Lambda consumes and updates a DynamoDB current-state table. Demonstrates scalable async patterns.

**AWS quick facts**
- Region: eu-west-1
- Free-tier friendly: SQS (1M requests), Lambda, DynamoDB
- Producer can be run locally or in CloudShell.

**Structure**
infra/           # SAM template (SQS, Lambda, DynamoDB)

producer/        # producer/producer.py (CloudShell ready)

consumer/        # Lambda consumer

scripts/         # deploy.sh

diagrams/        # architecture

evidence/        # sample event logs + occupancy snapshots

**How to run (summary)**
1. Deploy infra with SAM.
2. Run the producer script (optionally in CloudShell) to send events.
3. Monitor DynamoDB for occupancy and S3 for logs.

**Evidence to collect**
- SQS queue attributes
- Lambda invocation logs
- DynamoDB items representing current occupancy

**Notes**
This project provides a small-scale event-driven demonstration relevant to logistics and healthcare operations.
