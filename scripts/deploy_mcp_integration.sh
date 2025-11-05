#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/ial
REGION=${AWS_DEFAULT_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🚀 Deploying IAL MCP Integration..."

# 1. Deploy MCP Lambda wrappers
echo "🔧 Deploying MCP Lambda wrappers..."
MCP_LAMBDAS=("wa_mcp" "finops_mcp" "compliance_runner" "policy_checks" "github_mcp")

for wrapper in "${MCP_LAMBDAS[@]}"; do
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
      --memory-size 512 \
      --region $REGION
  fi
  
  rm ${wrapper}_wrapper.zip
done

# 2. Create CFN-Guard Lambda with different handler
echo "Creating CFN-Guard Lambda with guard_handler..."
FUNCTION_NAME="ial-policy-cfnguard-lambda"
cd $ROOT/lambdas/wrappers
zip -r policy_checks_guard.zip policy_checks_wrapper.py

if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION >/dev/null 2>&1; then
  echo "Updating $FUNCTION_NAME..."
  aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://policy_checks_guard.zip \
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
    --handler policy_checks_wrapper.guard_handler \
    --zip-file fileb://policy_checks_guard.zip \
    --timeout 300 \
    --memory-size 256 \
    --region $REGION
fi

rm policy_checks_guard.zip

# 3. Create Reverse Sync State Machine
echo "⚙️ Creating Reverse Sync state machine..."

ASL_FILE=$ROOT/stepfunctions/reverse_sync.asl.json
TEMP_ASL=/tmp/reverse_sync_resolved.asl.json

cp $ASL_FILE $TEMP_ASL

# Replace ARN placeholders
sed -i "s|\${IAL_REVERSE_SYNC_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-reverse-sync-lambda|g" $TEMP_ASL
sed -i "s|\${IAL_GITHUB_MCP_WRAPPER_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-github-mcp-lambda|g" $TEMP_ASL
sed -i "s|\${IAL_AUDIT_VALIDATOR_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-audit-validator-lambda|g" $TEMP_ASL

# Create Standard state machine
STATE_MACHINE_NAME="ial-reverse-sync"
SFN_ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name ial-stepfunctions-roles \
  --query 'Stacks[0].Outputs[?OutputKey==`StepFunctionsRoleArn`].OutputValue' \
  --output text \
  --region $REGION)

if aws stepfunctions describe-state-machine --state-machine-arn "arn:aws:states:$REGION:$ACCOUNT_ID:stateMachine:$STATE_MACHINE_NAME" --region $REGION >/dev/null 2>&1; then
  echo "Updating reverse sync state machine..."
  aws stepfunctions update-state-machine \
    --state-machine-arn "arn:aws:states:$REGION:$ACCOUNT_ID:stateMachine:$STATE_MACHINE_NAME" \
    --definition file://$TEMP_ASL \
    --region $REGION
else
  echo "Creating reverse sync state machine..."
  aws stepfunctions create-state-machine \
    --name $STATE_MACHINE_NAME \
    --definition file://$TEMP_ASL \
    --role-arn $SFN_ROLE_ARN \
    --type STANDARD \
    --region $REGION
fi

# 4. Update Phase Pipeline with MCP ARNs
echo "🔄 Updating Phase Pipeline with MCP ARNs..."
PHASE_ASL_FILE=$ROOT/stepfunctions/phase_pipeline.asl.json
TEMP_PHASE_ASL=/tmp/phase_pipeline_mcp_resolved.asl.json

cp $PHASE_ASL_FILE $TEMP_PHASE_ASL

# Replace MCP ARN placeholders
sed -i "s|\${IAL_WA_MCP_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-wa-mcp-lambda|g" $TEMP_PHASE_ASL
sed -i "s|\${IAL_FINOPS_MCP_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-finops-mcp-lambda|g" $TEMP_PHASE_ASL
sed -i "s|\${IAL_COMPLIANCE_RUNNER_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-compliance-runner-lambda|g" $TEMP_PHASE_ASL
sed -i "s|\${IAL_POLICY_OPA_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-policy-checks-lambda|g" $TEMP_PHASE_ASL
sed -i "s|\${IAL_POLICY_CFN_GUARD_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-policy-cfnguard-lambda|g" $TEMP_PHASE_ASL

# Update existing ARNs
sed -i "s|\${IAL_CIRCUIT_GUARD_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-circuit-guard-lambda|g" $TEMP_PHASE_ASL
sed -i "s|\${IAL_PLAN_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-plan-lambda|g" $TEMP_PHASE_ASL
sed -i "s|\${IAL_APPLY_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-apply-lambda|g" $TEMP_PHASE_ASL
sed -i "s|\${IAL_AUDIT_VALIDATOR_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-audit-validator-lambda|g" $TEMP_PHASE_ASL
sed -i "s|\${IAL_ROLLBACK_ARN}|arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-rollback-lambda|g" $TEMP_PHASE_ASL

# Update phase pipeline
aws stepfunctions update-state-machine \
  --state-machine-arn "arn:aws:states:$REGION:$ACCOUNT_ID:stateMachine:ial-phase-pipeline" \
  --definition file://$TEMP_PHASE_ASL \
  --region $REGION

# 5. Generate deployment report
echo "📋 Generating MCP integration report..."
cat > $ROOT/reports/sfn/mcp_integration_report.json << EOF
{
  "deployment_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
  "region": "$REGION",
  "account_id": "$ACCOUNT_ID",
  "mcp_integration": {
    "reverse_sync_state_machine": "arn:aws:states:$REGION:$ACCOUNT_ID:stateMachine:ial-reverse-sync",
    "phase_pipeline_updated": true
  },
  "mcp_lambda_functions": [
$(for wrapper in "${MCP_LAMBDAS[@]}"; do
  name="ial-${wrapper//_/-}-lambda"
  arn="arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$name"
  echo "    {\"name\": \"$name\", \"arn\": \"$arn\"},"
done
echo "    {\"name\": \"ial-policy-cfnguard-lambda\", \"arn\": \"arn:aws:lambda:$REGION:$ACCOUNT_ID:function:ial-policy-cfnguard-lambda\"}"
)
  ],
  "mcp_capabilities": [
    "Well-Architected reviews with scoring",
    "FinOps cost analysis and optimization",
    "Compliance checks with violation reporting",
    "Policy validation (OPA + CFN-Guard)",
    "GitHub PR automation (placeholder)"
  ],
  "status": "SUCCESS"
}
EOF

echo "✅ MCP Integration deployment completed!"
echo "Reverse Sync ARN: arn:aws:states:$REGION:$ACCOUNT_ID:stateMachine:ial-reverse-sync"
echo "Report: $ROOT/reports/sfn/mcp_integration_report.json"
