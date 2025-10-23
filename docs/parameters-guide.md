# 🔧 PARAMETERS GUIDE

Complete guide to configuring parameters for this AWS Reference Pattern.

---

## 📋 REQUIRED PARAMETERS

### AWS_ACCOUNT_ID
- **Description**: Your 12-digit AWS account ID
- **Format**: `123456789012`
- **How to find**: `aws sts get-caller-identity --query Account --output text`
- **Example**: `221082174220`

### AWS_REGION
- **Description**: AWS region for deployment
- **Format**: `us-east-1`, `eu-west-1`, etc
- **Supported**: Any region with ECS Fargate + ElastiCache Serverless
- **Example**: `us-east-1`

### PROJECT_NAME
- **Description**: Unique name for your project (used as prefix for all resources)
- **Format**: Lowercase, alphanumeric, hyphens allowed, no spaces
- **Length**: 3-30 characters
- **Example**: `my-awesome-app`, `spring-redis-prod`
- **Used in**: Resource names, tags, Parameter Store paths

### EXECUTOR_NAME
- **Description**: Your name or team name (for tracking and auditing)
- **Format**: Alphanumeric, hyphens allowed
- **Example**: `JohnDoe`, `DevOps-Team`
- **Used in**: Resource tags (Executor tag)

---

## 📝 CONFIGURATION FILE

### Create parameters.env
```bash
cp parameters.env.example parameters.env
nano parameters.env
```

### Example Configuration
```bash
# AWS Account Configuration
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1

# Project Configuration
PROJECT_NAME=my-spring-app
EXECUTOR_NAME=JohnDoe
```

---

## 🔒 SECURITY

### parameters.env File
- ❌ **NEVER commit** to Git
- ✅ Already in `.gitignore`
- ✅ Each developer has their own
- ✅ Use `parameters.env.example` as template

### Sensitive Data
- `AWS_ACCOUNT_ID`: Identifies your account (not secret, but private)
- `EXECUTOR_NAME`: Your name (for tracking)
- `PROJECT_NAME`: Project name (can be public)
- `AWS_REGION`: Region (not secret)

**Note**: No actual secrets (passwords, keys) are stored in parameters.env.

---

## 🌍 MULTI-ENVIRONMENT SETUP

### Development Environment
```bash
# parameters.dev.env
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
PROJECT_NAME=myapp-dev
EXECUTOR_NAME=DevTeam
```

### Staging Environment
```bash
# parameters.staging.env
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
PROJECT_NAME=myapp-staging
EXECUTOR_NAME=QATeam
```

### Production Environment
```bash
# parameters.prod.env
AWS_ACCOUNT_ID=987654321098  # Different account
AWS_REGION=us-east-1
PROJECT_NAME=myapp-prod
EXECUTOR_NAME=OpsTeam
```

---

## 🔄 USING PARAMETERS

### Load Parameters
```bash
# Export as environment variables
export AWS_ACCOUNT_ID=123456789012
export AWS_REGION=us-east-1
export PROJECT_NAME=my-app
export EXECUTOR_NAME=YourName
```

### Process YAML Files
```bash
# Replace placeholders in YAML
sed "s/{{AWS_ACCOUNT_ID}}/$AWS_ACCOUNT_ID/g" phases/00-dynamodb-state.yaml | \
sed "s/{{AWS_REGION}}/$AWS_REGION/g" | \
sed "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" | \
sed "s/{{EXECUTOR_NAME}}/$EXECUTOR_NAME/g"
```

### Execute Commands
- Copy AWS CLI commands from processed YAML
- Execute manually in terminal
- Validate resources created

---

## ✅ VALIDATION

### Verify Parameters
```bash
# Check if all required parameters are set
echo "Account: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"
echo "Project: $PROJECT_NAME"
echo "Executor: $EXECUTOR_NAME"

# Verify AWS credentials
aws sts get-caller-identity

# Verify region is valid
aws ec2 describe-regions --query "Regions[?RegionName=='$AWS_REGION'].RegionName" --output text
```

---

## 🚨 COMMON MISTAKES

### 1. Wrong Account ID Format
```bash
❌ AWS_ACCOUNT_ID=221-082-174-220  # With dashes
❌ AWS_ACCOUNT_ID="221082174220"   # With quotes
✅ AWS_ACCOUNT_ID=221082174220     # Correct
```

### 2. Invalid Project Name
```bash
❌ PROJECT_NAME=My App             # Spaces not allowed
❌ PROJECT_NAME=my_app             # Underscores not recommended
✅ PROJECT_NAME=my-app             # Correct
```

### 3. Region Not Supported
```bash
❌ AWS_REGION=us-east-1a           # AZ, not region
✅ AWS_REGION=us-east-1            # Correct
```

---

## 📚 NEXT STEPS

After configuring parameters:
1. [Quick Start](../QUICK_START.md) - Deploy first resource
2. [Deployment Guide](deployment-guide.md) - Full deployment
3. [Validation Guide](validation-guide.md) - Verify resources
