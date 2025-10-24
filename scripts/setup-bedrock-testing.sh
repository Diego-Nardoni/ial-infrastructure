#!/bin/bash
# Setup Bedrock Testing for IaL Project

echo "🧠 Setting up Bedrock Intelligent Testing..."

# Create required directories
mkdir -p /home/ial/{tests/generated,reports,logs}

# Make scripts executable
chmod +x /home/ial/scripts/bedrock-*.py

# Install Python dependencies (using --break-system-packages for this environment)
pip3 install boto3 pytest pytest-json-report --break-system-packages

echo "✅ Bedrock Testing setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Enable Bedrock models in AWS Console:"
echo "   - anthropic.claude-3-sonnet-20240229-v1:0"
echo "   - anthropic.claude-3-haiku-20240307-v1:0"
echo ""
echo "2. Add Bedrock permissions to GitHub Actions role"
echo ""
echo "3. Test implementation:"
echo "   python3 /home/ial/scripts/bedrock-test-generator.py"
echo ""
echo "4. Commit and push to trigger CI/CD with Bedrock testing"
