#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/ial
REGION=${AWS_DEFAULT_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🚀 Deploying IAL Step Functions..."
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"

# 1. Deploy IAM Roles
echo "📋 Deploying IAM roles..."
aws cloudformation deploy \
  --template-file $ROOT/iam/sfn_roles.yaml \
  --stack-name ial-stepfunctions-roles \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

aws cloudformation deploy \
  --template-file $ROOT/iam/lambda_roles.yaml \
  --stack-name ial-lambda-roles \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

# 2. Get Role ARNs
SFN_ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name ial-stepfunctions-roles \
  --query 'Stacks[0].Outputs[?OutputKey==`StepFunctionsRoleArn`].OutputValue' \
  --output text \
  --region $REGION)

LAMBDA_ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name ial-lambda-roles \
  --query 'Stacks[0].Outputs[?OutputKey==`LambdaExecutionRoleArn`].OutputValue' \
  --output text \
  --region $REGION)

echo "SFN Role ARN: $SFN_ROLE_ARN"
echo "Lambda Role ARN: $LAMBDA_ROLE_ARN"

# 3. Create/Update Lambda Functions
echo "🔧 Deploying Lambda wrappers..."
LAMBDA_ARNS=()

for wrapper in circuit_guard plan apply audit_validator rollback; do
  FUNCTION_NAME="ial-${wrapper}-lambda"
  
  # Create deployment package
  cd $ROOT/lambdas/wrappers
  zip -r ${wrapper}_wrapper.zip ${wrapper}_wrapper.py
  
  # Create or update function
  if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION >/dev/null 2>&1; then
    echo "Updating $FUNCTION_NAME..."
    aws lambda update-function-code \
      --function-name $FUNCTION_NAME \
      --zip-file fileb://${wrapper}_wrapper.zip \
      --region $REGION
  else
    echo "Creating $FUNCTION_NAME..."
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
  
  # Get ARN
  LAMBDA_ARN=$(aws lambda get-function \
    --function-name $FUNCTION_NAME \
    --query 'Configuration.FunctionArn' \
    --output text \
    --region $REGION)
  
  LAMBDA_ARNS+=("$FUNCTION_NAME:$LAMBDA_ARN")
  
  # Cleanup
  rm ${wrapper}_wrapper.zip
done

# 4. Create Step Functions State Machine
echo "⚙️ Creating Step Functions state machine..."

# Replace ARN placeholders in ASL
ASL_FILE=$ROOT/stepfunctions/phase_pipeline.asl.json
TEMP_ASL=/tmp/phase_pipeline_resolved.asl.json

cp $ASL_FILE $TEMP_ASL

# Replace placeholders with actual ARNs
for lambda_info in "${LAMBDA_ARNS[@]}"; do
  name=$(echo $lambda_info | cut -d: -f1)
  arn=$(echo $lambda_info | cut -d: -f2-)
  
  case $name in
    "ial-circuit-guard-lambda")
      sed -i "s|\${IAL_CIRCUIT_GUARD_ARN}|$arn|g" $TEMP_ASL
      ;;
    "ial-plan-lambda")
      sed -i "s|\${IAL_PLAN_ARN}|$arn|g" $TEMP_ASL
      ;;
    "ial-apply-lambda")
      sed -i "s|\${IAL_APPLY_ARN}|$arn|g" $TEMP_ASL
      ;;
    "ial-audit-validator-lambda")
      sed -i "s|\${IAL_AUDIT_VALIDATOR_ARN}|$arn|g" $TEMP_ASL
      ;;
    "ial-rollback-lambda")
      sed -i "s|\${IAL_ROLLBACK_ARN}|$arn|g" $TEMP_ASL
      ;;
  esac
done

# Add placeholder ARNs for missing functions
sed -i "s|\${IAL_POLICY_OPA_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-policy-opa-lambda|g" $TEMP_ASL
sed -i "s|\${IAL_POLICY_CFN_GUARD_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-policy-cfnguard-lambda|g" $TEMP_ASL
sed -i "s|\${IAL_WA_MCP_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-wa-mcp-lambda|g" $TEMP_ASL
sed -i "s|\${IAL_FINOPS_MCP_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-finops-mcp-lambda|g" $TEMP_ASL
sed -i "s|\${IAL_COMPLIANCE_RUNNER_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-compliance-runner-lambda|g" $TEMP_ASL

# Create state machine
STATE_MACHINE_NAME="ial-phase-pipeline"
if aws stepfunctions describe-state-machine --state-machine-arn "arn:aws:states:$REGION:$ACCOUNT_ID:stateMachine:$STATE_MACHINE_NAME" --region $REGION >/dev/null 2>&1; then
  echo "Updating state machine..."
  aws stepfunctions update-state-machine \
    --state-machine-arn "arn:aws:states:$REGION:$ACCOUNT_ID:stateMachine:$STATE_MACHINE_NAME" \
    --definition file://$TEMP_ASL \
    --region $REGION
else
  echo "Creating state machine..."
  aws stepfunctions create-state-machine \
    --name $STATE_MACHINE_NAME \
    --definition file://$TEMP_ASL \
    --role-arn $SFN_ROLE_ARN \
    --region $REGION
fi

STATE_MACHINE_ARN="arn:aws:states:$REGION:$ACCOUNT_ID:stateMachine:$STATE_MACHINE_NAME"

# 5. Generate deployment report
echo "📊 Generating deployment report..."
mkdir -p $ROOT/reports/sfn

cat > $ROOT/reports/sfn/last_deploy_report.json << EOF
{
  "deployment_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
  "region": "$REGION",
  "account_id": "$ACCOUNT_ID",
  "step_functions": {
    "state_machine_name": "$STATE_MACHINE_NAME",
    "state_machine_arn": "$STATE_MACHINE_ARN",
    "role_arn": "$SFN_ROLE_ARN"
  },
  "lambda_functions": [
$(for lambda_info in "${LAMBDA_ARNS[@]}"; do
  name=$(echo $lambda_info | cut -d: -f1)
  arn=$(echo $lambda_info | cut -d: -f2-)
  echo "    {\"name\": \"$name\", \"arn\": \"$arn\"},"
done | sed '$ s/,$//')
  ],
  "status": "SUCCESS"
}
EOF

echo "✅ Deployment completed successfully!"
echo "State Machine ARN: $STATE_MACHINE_ARN"
echo "Report: $ROOT/reports/sfn/last_deploy_report.json"
