#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/ial
REGION=${AWS_DEFAULT_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🚀 Deploying IAL Drift Automation..."

# 1. Deploy additional Lambda wrappers
echo "🔧 Deploying drift Lambda wrappers..."
DRIFT_LAMBDAS=("drift_flag_check" "drift_detect" "drift_reconcile" "reverse_sync" "metrics_publisher")

for wrapper in "${DRIFT_LAMBDAS[@]}"; do
  FUNCTION_NAME="ial-${wrapper//_/-}-lambda"
  
  cd $ROOT/lambdas/wrappers
  zip -r ${wrapper}_wrapper.zip ${wrapper}_wrapper.py
  
  if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION >/dev/null 2>&1; then
    echo "Updating $FUNCTION_NAME..."
    aws lambda update-function-code \
      --function-name $FUNCTION_NAME \
      --zip-file fileb://${wrapper}_wrapper.zip \
      --region $REGION
  else
    echo "Creating $FUNCTION_NAME..."
    LAMBDA_ROLE_ARN=$(aws cloudformation describe-stacks \
      --stack-name ial-lambda-roles \
      --query 'Stacks[0].Outputs[?OutputKey==`LambdaExecutionRoleArn`].OutputValue' \
      --output text \
      --region $REGION)
    
    aws lambda create-function \
      --function-name $FUNCTION_NAME \
      --runtime python3.9 \
      --role $LAMBDA_ROLE_ARN \
      --handler ${wrapper}_wrapper.lambda_handler \
      --zip-file fileb://${wrapper}_wrapper.zip \
      --timeout 300 \
      --memory-size 256 \
      --region $REGION
  fi
  
  rm ${wrapper}_wrapper.zip
done

# 2. Create Drift Auto-Heal State Machine
echo "⚙️ Creating Drift Auto-Heal state machine..."

ASL_FILE=$ROOT/stepfunctions/drift_autoheal.asl.json
TEMP_ASL=/tmp/drift_autoheal_resolved.asl.json

cp $ASL_FILE $TEMP_ASL

# Replace ARN placeholders
sed -i "s|\${IAL_DRIFT_FLAG_CHECK_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-drift-flag-check-lambda|g" $TEMP_ASL
sed -i "s|\${IAL_DRIFT_DETECT_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-drift-detect-lambda|g" $TEMP_ASL
sed -i "s|\${IAL_DRIFT_RECONCILE_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-drift-reconcile-lambda|g" $TEMP_ASL
sed -i "s|\${IAL_REVERSE_SYNC_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-reverse-sync-lambda|g" $TEMP_ASL

# Create Express state machine
STATE_MACHINE_NAME="ial-drift-autoheal"
SFN_ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name ial-stepfunctions-roles \
  --query 'Stacks[0].Outputs[?OutputKey==`StepFunctionsRoleArn`].OutputValue' \
  --output text \
  --region $REGION)

if aws stepfunctions describe-state-machine --state-machine-arn "arn:aws:states:$REGION:$ACCOUNT_ID:stateMachine:$STATE_MACHINE_NAME" --region $REGION >/dev/null 2>&1; then
  echo "Updating drift auto-heal state machine..."
  aws stepfunctions update-state-machine \
    --state-machine-arn "arn:aws:states:$REGION:$ACCOUNT_ID:stateMachine:$STATE_MACHINE_NAME" \
    --definition file://$TEMP_ASL \
    --region $REGION
else
  echo "Creating drift auto-heal state machine..."
  aws stepfunctions create-state-machine \
    --name $STATE_MACHINE_NAME \
    --definition file://$TEMP_ASL \
    --role-arn $SFN_ROLE_ARN \
    --type EXPRESS \
    --region $REGION
fi

# 3. Deploy EventBridge rule
echo "📅 Deploying EventBridge rule..."
aws cloudformation deploy \
  --template-file $ROOT/iam/events_rules.yaml \
  --stack-name ial-eventbridge-rules \
  --parameter-overrides StepFunctionsRoleArn=$SFN_ROLE_ARN \
  --region $REGION

# 4. Deploy CloudWatch alarms
echo "📊 Deploying CloudWatch alarms..."
aws cloudformation deploy \
  --template-file $ROOT/config/stepfunctions/cloudwatch_alarms.yaml \
  --stack-name ial-cloudwatch-alarms \
  --region $REGION

# 5. Update deployment report
echo "📋 Updating deployment report..."
cat > $ROOT/reports/sfn/drift_automation_report.json << EOF
{
  "deployment_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
  "region": "$REGION",
  "account_id": "$ACCOUNT_ID",
  "drift_automation": {
    "state_machine_name": "$STATE_MACHINE_NAME",
    "state_machine_arn": "arn:aws:states:$REGION:$ACCOUNT_ID:stateMachine:$STATE_MACHINE_NAME",
    "type": "EXPRESS",
    "eventbridge_rule": "ial-drift-scanner",
    "schedule": "rate(15 minutes)"
  },
  "lambda_functions": [
$(for wrapper in "${DRIFT_LAMBDAS[@]}"; do
  name="ial-${wrapper//_/-}-lambda"
  arn="arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$name"
  echo "    {\"name\": \"$name\", \"arn\": \"$arn\"},"
done | sed '$ s/,$//')
  ],
  "cloudwatch_alarms": [
    "IAL-CircuitBreaker-Open",
    "IAL-CreationCompleteness-Low", 
    "IAL-StepFunctions-Failures",
    "IAL-DriftDetection-High"
  ],
  "status": "SUCCESS"
}
EOF

echo "✅ Drift automation deployment completed!"
echo "State Machine ARN: arn:aws:states:$REGION:$ACCOUNT_ID:stateMachine:$STATE_MACHINE_NAME"
echo "Report: $ROOT/reports/sfn/drift_automation_report.json"
