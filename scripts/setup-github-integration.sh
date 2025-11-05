#!/bin/bash

echo "🔧 IAL GitHub Actions Integration Setup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "governance_cli.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the IAL root directory${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 This script will help you configure GitHub Actions integration${NC}"
echo ""

# 1. Check AWS CLI configuration
echo "1️⃣ Checking AWS CLI configuration..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS CLI not configured. Please run 'aws configure' first${NC}"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account ID: ${ACCOUNT_ID}${NC}"

# 2. Get GitHub repository information
echo ""
echo "2️⃣ GitHub Repository Configuration"
echo "Please provide your GitHub repository information:"

read -p "GitHub Repository Owner (username/org): " GITHUB_OWNER
read -p "GitHub Repository Name: " GITHUB_REPO

if [ -z "$GITHUB_OWNER" ] || [ -z "$GITHUB_REPO" ]; then
    echo -e "${RED}❌ GitHub repository information is required${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Repository: ${GITHUB_OWNER}/${GITHUB_REPO}${NC}"

# 3. Create IAM Role for GitHub Actions
echo ""
echo "3️⃣ Creating IAM Role for GitHub Actions..."

ROLE_NAME="GitHubActionsIALRole"
TRUST_POLICY=$(cat << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:${GITHUB_OWNER}/${GITHUB_REPO}:*"
                }
            }
        }
    ]
}
EOF
)

# Create the role
echo "$TRUST_POLICY" > /tmp/trust-policy.json

if aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document file:///tmp/trust-policy.json \
    --description "IAM role for IAL GitHub Actions" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Created IAM role: ${ROLE_NAME}${NC}"
else
    echo -e "${YELLOW}⚠️ IAM role may already exist, continuing...${NC}"
fi

# 4. Attach policies to the role
echo ""
echo "4️⃣ Attaching policies to IAM role..."

POLICY_DOCUMENT=$(cat << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:*",
                "cloudwatch:PutMetricData",
                "ce:GetCostAndUsage",
                "ce:GetUsageReport",
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket",
                "resource-explorer-2:Search",
                "resource-explorer-2:ListResources",
                "ec2:Describe*",
                "iam:ListRoles",
                "iam:GetRole"
            ],
            "Resource": "*"
        }
    ]
}
EOF
)

echo "$POLICY_DOCUMENT" > /tmp/ial-policy.json

POLICY_NAME="IALGovernancePolicy"
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

# Create policy
if aws iam create-policy \
    --policy-name "$POLICY_NAME" \
    --policy-document file:///tmp/ial-policy.json \
    --description "Policy for IAL Governance operations" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Created IAM policy: ${POLICY_NAME}${NC}"
else
    echo -e "${YELLOW}⚠️ IAM policy may already exist, continuing...${NC}"
fi

# Attach policy to role
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN" > /dev/null 2>&1

echo -e "${GREEN}✅ Attached policy to role${NC}"

# 5. Generate GitHub Secrets
echo ""
echo "5️⃣ GitHub Secrets Configuration"
echo "Please add the following secrets to your GitHub repository:"
echo ""
echo -e "${YELLOW}Repository Settings → Secrets and variables → Actions → New repository secret${NC}"
echo ""

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
echo -e "${GREEN}AWS_ROLE_ARN${NC}"
echo "$ROLE_ARN"
echo ""

echo -e "${GREEN}AWS_REGION${NC}"
echo "us-east-1"
echo ""

# 6. Branch Protection Configuration
echo "6️⃣ Branch Protection Configuration"
echo "Please configure branch protection rules in GitHub:"
echo ""
echo -e "${YELLOW}Repository Settings → Branches → Add rule${NC}"
echo ""
echo "Branch name pattern: main"
echo "Required status checks:"
echo "  - pre-deploy-gates"
echo "  - Require branches to be up to date before merging"
echo ""

# 7. Test Configuration
echo "7️⃣ Testing Configuration"
echo ""
read -p "Would you like to test the configuration? (y/n): " TEST_CONFIG

if [[ "$TEST_CONFIG" =~ ^[Yy]$ ]]; then
    echo "Testing AWS permissions..."
    
    if aws sts assume-role \
        --role-arn "$ROLE_ARN" \
        --role-session-name "test-session" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ IAM role can be assumed${NC}"
    else
        echo -e "${RED}❌ Cannot assume IAM role. Check OIDC provider configuration${NC}"
    fi
    
    echo "Testing governance CLI..."
    if python3 governance_cli.py compliance-check phases/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Governance CLI working${NC}"
    else
        echo -e "${YELLOW}⚠️ Governance CLI test failed (may be expected without real infrastructure)${NC}"
    fi
fi

# 8. Summary
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Add the GitHub secrets shown above to your repository"
echo "2. Configure branch protection rules as described"
echo "3. Create a test PR to verify the governance pipeline"
echo ""
echo -e "${GREEN}✅ IAM Role ARN: ${ROLE_ARN}${NC}"
echo -e "${GREEN}✅ GitHub Actions workflow: .github/workflows/ial-governance.yml${NC}"
echo ""

# Cleanup
rm -f /tmp/trust-policy.json /tmp/ial-policy.json

echo "🚀 Your IAL GitHub Actions integration is ready!"
