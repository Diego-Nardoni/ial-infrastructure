#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/ial
REGION=${AWS_DEFAULT_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "📊 Creating IAL CloudWatch Dashboard..."

# Replace ACCOUNT_ID placeholder in dashboard JSON
DASHBOARD_FILE=$ROOT/config/stepfunctions/cloudwatch_dashboard.json
TEMP_DASHBOARD=/tmp/ial_dashboard.json

sed "s/ACCOUNT_ID/$ACCOUNT_ID/g" $DASHBOARD_FILE > $TEMP_DASHBOARD

# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name "IAL-StepFunctions-Operations" \
  --dashboard-body file://$TEMP_DASHBOARD \
  --region $REGION

echo "✅ Dashboard created successfully!"
echo "URL: https://$REGION.console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:name=IAL-StepFunctions-Operations"

# Cleanup
rm $TEMP_DASHBOARD
