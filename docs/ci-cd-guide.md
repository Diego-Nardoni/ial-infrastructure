# 🔗 CI/CD Guide - IaL Evolution v2.0

## Overview

GitHub Actions automates infrastructure deployment with state locking, reconciliation, and drift detection.

## Workflows

### 1. Deploy (deploy.yml)
- **Trigger**: Push to `main` branch with changes in `phases/**/*.yaml`
- **Steps**:
  1. Acquire DynamoDB lock
  2. Run reconciliation
  3. Release lock
  4. Send SNS notification

### 2. Drift Detection (drift-detection.yml)
- **Trigger**: Hourly cron + manual dispatch
- **Steps**:
  1. Query all resources
  2. Compare desired vs current state
  3. Classify severity with Bedrock
  4. Notify if drifts found

### 3. Rollback (rollback.yml)
- **Trigger**: Manual workflow dispatch
- **Input**: Target commit SHA
- **Steps**:
  1. Execute rollback script
  2. Git revert changes
  3. Push to main

## Setup

### 1. GitHub Secrets
```bash
AWS_ACCOUNT_ID=123456789012
```

### 2. AWS IAM Role
Create OIDC role: `GitHubActionsRole-IaL-Infrastructure`

Permissions:
- EC2, ECS, ALB, ElastiCache, CloudFront, WAF
- DynamoDB (mcp-provisioning-checklist)
- SNS (alerts-critical)
- Bedrock (invoke model)

### 3. Repository Settings
- Enable Actions
- Configure OIDC provider
- Set branch protection rules

## Usage

### Automatic Deploy
```bash
git add phases/03-networking.yaml
git commit -m "Add port 8443 to ALB SG"
git push
# GitHub Actions deploys automatically
```

### Manual Drift Check
```bash
# Via GitHub UI: Actions → Drift Detection → Run workflow
```

### Rollback
```bash
# Via GitHub UI: Actions → Rollback → Run workflow
# Input: commit SHA to rollback to
```

## State Locking

DynamoDB Conditional Write ensures only one deployment runs:
```python
--condition-expression 'attribute_not_exists(ResourceName)'
```

Lock auto-releases after 30 minutes (TTL).

## Notifications

SNS email sent on:
- Deploy success/failure
- Drift detection (CRITICAL/HIGH only)
- Rollback completion

## Cost

- GitHub Actions: $0 (free tier)
- Additional API calls: ~$0.10/month
