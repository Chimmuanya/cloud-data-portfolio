#!/usr/bin/env bash
# scripts/deploy/rollback_stack.sh
#
# Project 3 — Stack Rollback Helper

set -euo pipefail

AWS_PROFILE="${AWS_PROFILE:-deploy-ci}"
AWS_REGION="${AWS_REGION:-eu-west-1}"
STACK_NAME="${STACK_NAME:-project-03-public-health-datalake}"

echo "⚠️  Rolling back CloudFormation stack"
echo "Stack   : ${STACK_NAME}"
echo "Region  : ${AWS_REGION}"
echo "Profile : ${AWS_PROFILE}"
echo

aws cloudformation delete-stack \
  --stack-name "${STACK_NAME}" \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}"

echo "Rollback initiated."
echo "Monitor progress via AWS Console or:"
echo "aws cloudformation describe-stacks --stack-name ${STACK_NAME}"
