#!/bin/bash
echo "🔧 Deploying CloudTrail Monitor..."

# Deploy CloudFormation stack
aws cloudformation deploy \
  --template-file infrastructure/cloudtrail-monitor-setup.yaml \
  --stack-name ial-cloudtrail-monitor \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides ProjectName=ial

if [ $? -eq 0 ]; then
    echo "✅ CloudTrail monitor deployed successfully"
    
    # Get Lambda function name
    FUNCTION_NAME=$(aws cloudformation describe-stacks \
      --stack-name ial-cloudtrail-monitor \
      --query 'Stacks[0].Outputs[?OutputKey==`ProcessorFunctionArn`].OutputValue' \
      --output text | cut -d':' -f7)
    
    # Update Lambda function code
    echo "📦 Updating Lambda function code..."
    cd /home/ial/lambda/cloudtrail-processor
    zip -r function.zip . > /dev/null
    
    aws lambda update-function-code \
      --function-name $FUNCTION_NAME \
      --zip-file fileb://function.zip > /dev/null
    
    rm function.zip
    
    echo "✅ Lambda function updated"
    echo "💰 Estimated cost: $0.05-0.15/month"
else
    echo "❌ CloudTrail monitor deployment failed"
fi
