#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/ial
REGION=${AWS_DEFAULT_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🧪 Testing IAL Step Functions..."

# 1. Create SSM parameters for circuit breaker
echo "📋 Setting up SSM parameters..."
aws ssm put-parameter \
  --name "/ial/circuit_breaker/state" \
  --value "closed" \
  --type "String" \
  --description "Circuit breaker state" \
  --overwrite \
  --region $REGION

aws ssm put-parameter \
  --name "/ial/circuit_breaker/max_inflight" \
  --value "3" \
  --type "String" \
  --description "Maximum concurrent executions" \
  --overwrite \
  --region $REGION

aws ssm put-parameter \
  --name "/ial/circuit_breaker/retry_after_sec" \
  --value "120" \
  --type "String" \
  --description "Retry after seconds when circuit is open" \
  --overwrite \
  --region $REGION

# 2. Test payload
TEST_PAYLOAD='{
  "phase": "00-foundation",
  "region": "us-east-1",
  "stack": "ial-foundation-test",
  "changeset_name": "test-changeset"
}'

# 3. Start execution
echo "🚀 Starting Step Functions execution..."
STATE_MACHINE_ARN="arn:aws:states:$REGION:$ACCOUNT_ID:stateMachine:ial-phase-pipeline"

EXECUTION_ARN=$(aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --name "test-execution-$(date +%s)" \
  --input "$TEST_PAYLOAD" \
  --query 'executionArn' \
  --output text \
  --region $REGION)

echo "Execution ARN: $EXECUTION_ARN"

# 4. Wait for completion (max 5 minutes)
echo "⏳ Waiting for execution to complete..."
for i in {1..30}; do
  STATUS=$(aws stepfunctions describe-execution \
    --execution-arn $EXECUTION_ARN \
    --query 'status' \
    --output text \
    --region $REGION)
  
  echo "Status: $STATUS (attempt $i/30)"
  
  if [[ "$STATUS" == "SUCCEEDED" ]]; then
    echo "✅ Execution completed successfully!"
    break
  elif [[ "$STATUS" == "FAILED" ]]; then
    echo "❌ Execution failed!"
    aws stepfunctions describe-execution \
      --execution-arn $EXECUTION_ARN \
      --region $REGION
    exit 1
  elif [[ "$STATUS" == "ABORTED" ]]; then
    echo "⚠️ Execution aborted!"
    exit 1
  fi
  
  sleep 10
done

if [[ "$STATUS" == "RUNNING" ]]; then
  echo "⏰ Execution still running after 5 minutes - check manually"
  echo "Execution ARN: $EXECUTION_ARN"
fi

# 5. Get execution history
echo "📊 Getting execution history..."
aws stepfunctions get-execution-history \
  --execution-arn $EXECUTION_ARN \
  --region $REGION > $ROOT/reports/sfn/test_execution_history.json

echo "✅ Test completed!"
echo "History saved to: $ROOT/reports/sfn/test_execution_history.json"
