# GitHub OIDC Integration Setup

## Overview

This document explains how IAL integrates with GitHub Actions using OpenID Connect (OIDC) for secure, keyless authentication to AWS.

## Architecture

```
GitHub Actions → OIDC Token → AWS STS → Assume Role → Deploy Infrastructure
```

## Components

### 1. OIDC Identity Provider
- **URL**: `https://token.actions.githubusercontent.com`
- **Audiences**: `sts.amazonaws.com`
- **Thumbprints**: GitHub's certificate thumbprints (auto-updated)

### 2. IAM Role
- **Name**: `ial-github-actions-role`
- **Trust Policy**: Allows specific GitHub repositories
- **Permissions**: Limited by permissions boundary
- **Conditions**: Validates repo, branch, and environment

### 3. Security Features
- **Permissions Boundary**: Limits maximum permissions
- **Repository Validation**: Only authorized repos can assume role
- **Branch Restrictions**: Only specific branches allowed
- **Environment Controls**: Production environment validation

## Setup Process

### Automatic Setup (Recommended)
```bash
# IAL automatically configures OIDC during Control Plane deployment
ialctl init
# > ✅ OIDC Provider created
# > ✅ GitHub repo registered
# > ✅ Trust policy configured
```

### Manual Verification
```bash
# Check OIDC Provider
aws iam list-open-id-connect-providers

# Check IAM Role
aws iam get-role --role-name ial-github-actions-role

# Test assume role (from GitHub Actions)
aws sts assume-role-with-web-identity \
  --role-arn arn:aws:iam::ACCOUNT:role/ial-github-actions-role \
  --role-session-name test-session \
  --web-identity-token $ACTIONS_ID_TOKEN
```

## GitHub Actions Configuration

### Required Permissions
```yaml
permissions:
  id-token: write    # Required for OIDC
  contents: read     # Required for checkout
  pull-requests: write  # Optional for PR comments
```

### AWS Credentials Step
```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: us-east-1
    role-session-name: GitHubActions-${{ github.run_id }}
```

### Repository Secrets
- `AWS_ROLE_ARN`: ARN of the IAL GitHub Actions role

## Security Conditions

### Repository Validation
```json
{
  "StringLike": {
    "token.actions.githubusercontent.com:sub": [
      "repo:USER/ial-infrastructure:ref:refs/heads/main",
      "repo:USER/ial-infrastructure:environment:production"
    ]
  }
}
```

### Supported Patterns
- `repo:owner/repo:ref:refs/heads/main` - Specific branch
- `repo:owner/repo:environment:prod` - Specific environment
- `repo:owner/*:ref:refs/heads/main` - All repos from owner

## Multi-Repository Support

### Adding New Repository
```bash
# Via IAL CLI
ialctl github add-repo owner/new-repo

# Via AWS CLI
aws ssm put-parameter \
  --name "/ial/github/allowed_repos" \
  --value "repo:owner/repo1:*,repo:owner/repo2:*" \
  --type StringList \
  --overwrite
```

### Repository Patterns
- **Single Repo**: `repo:owner/ial-infrastructure:*`
- **All User Repos**: `repo:owner/*:*`
- **Specific Branch**: `repo:owner/repo:ref:refs/heads/main`
- **Environment**: `repo:owner/repo:environment:production`

## Troubleshooting

### Common Issues

#### 1. "No permission to assume role"
```bash
# Check trust policy
aws iam get-role --role-name ial-github-actions-role \
  --query 'Role.AssumeRolePolicyDocument'

# Verify repository is in allowed list
aws ssm get-parameter --name "/ial/github/allowed_repos"
```

#### 2. "Invalid identity token"
```yaml
# Ensure correct permissions in workflow
permissions:
  id-token: write
  contents: read
```

#### 3. "Token audience validation failed"
```yaml
# Verify audience in configure-aws-credentials
with:
  role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
  # audience defaults to 'sts.amazonaws.com' - usually correct
```

### Debug Commands

#### Check OIDC Provider
```bash
aws iam get-open-id-connect-provider \
  --open-id-connect-provider-arn arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com
```

#### Validate Role Trust Policy
```bash
aws iam get-role --role-name ial-github-actions-role \
  --query 'Role.AssumeRolePolicyDocument' \
  --output json | jq '.'
```

#### Test Token Claims (from GitHub Actions)
```bash
# Decode JWT token (for debugging)
echo $ACTIONS_ID_TOKEN | cut -d. -f2 | base64 -d | jq '.'
```

### CloudTrail Events
Monitor these events for OIDC activity:
- `AssumeRoleWithWebIdentity` - Role assumption attempts
- `GetOpenIDConnectProvider` - OIDC provider access
- `UpdateAssumeRolePolicy` - Trust policy changes

## Best Practices

### Security
1. **Least Privilege**: Use permissions boundary to limit maximum access
2. **Specific Conditions**: Avoid wildcard patterns in trust policy
3. **Environment Separation**: Use different roles for prod/dev
4. **Regular Rotation**: Update thumbprints when GitHub rotates certificates

### Operational
1. **Monitoring**: Set up CloudWatch alarms for failed assumptions
2. **Logging**: Enable CloudTrail for all IAM events
3. **Testing**: Validate OIDC integration in CI/CD pipeline
4. **Documentation**: Keep repository patterns updated

## Advanced Configuration

### Custom Trust Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:owner/repo:*"
        },
        "StringEquals": {
          "token.actions.githubusercontent.com:actor": "trusted-user"
        }
      }
    }
  ]
}
```

### Cross-Account Access
```yaml
# For deploying to different AWS accounts
- name: Configure AWS credentials for target account
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::TARGET-ACCOUNT:role/ial-cross-account-role
    aws-region: us-east-1
    role-chaining: true
```

## References
- [GitHub OIDC Documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [AWS IAM OIDC Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)
- [configure-aws-credentials Action](https://github.com/aws-actions/configure-aws-credentials)
