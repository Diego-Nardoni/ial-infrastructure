# Multi-Environment Deployment Example

Deploy the same infrastructure to multiple environments (dev, staging, production) using IaL parametrization.

## Overview

This example demonstrates how to deploy identical infrastructure across three environments with different configurations:

- **Development:** Minimal resources, lower costs
- **Staging:** Production-like, for testing
- **Production:** Full resources, high availability

---

## Environment Configurations

### Development Environment

**File:** `parameters-dev.env`

```bash
# AWS Configuration
export AWS_ACCOUNT_ID="123456789012"
export AWS_REGION="us-east-1"

# Project Configuration
export PROJECT_NAME="spring-redis-app-dev"
export EXECUTOR_NAME="dev-team"
export ENVIRONMENT="dev"

# ECS Configuration (Minimal)
export ECS_TASK_CPU="512"      # 0.5 vCPU
export ECS_TASK_MEMORY="1024"  # 1 GB
export ECS_DESIRED_COUNT="1"   # Single task
export ECS_MIN_CAPACITY="1"
export ECS_MAX_CAPACITY="2"

# Redis Configuration (Minimal)
export REDIS_MIN_STORAGE="1"
export REDIS_MAX_STORAGE="2"
export REDIS_MIN_ECPU="1000"
export REDIS_MAX_ECPU="2000"

# Cost Optimizations
export ENABLE_NAT_GATEWAY="false"  # Use VPC endpoints only
export ENABLE_CLOUDFRONT="false"   # Direct ALB access
export ENABLE_WAF="false"          # No WAF in dev
export CLOUDWATCH_RETENTION="3"    # 3 days
```

**Estimated Cost:** $80-120/month

---

### Staging Environment

**File:** `parameters-staging.env`

```bash
# AWS Configuration
export AWS_ACCOUNT_ID="123456789012"
export AWS_REGION="us-east-1"

# Project Configuration
export PROJECT_NAME="spring-redis-app-staging"
export EXECUTOR_NAME="staging-team"
export ENVIRONMENT="staging"

# ECS Configuration (Production-like)
export ECS_TASK_CPU="1024"     # 1 vCPU
export ECS_TASK_MEMORY="2048"  # 2 GB
export ECS_DESIRED_COUNT="2"   # 2 tasks
export ECS_MIN_CAPACITY="2"
export ECS_MAX_CAPACITY="5"

# Redis Configuration (Production-like)
export REDIS_MIN_STORAGE="1"
export REDIS_MAX_STORAGE="3"
export REDIS_MIN_ECPU="1000"
export REDIS_MAX_ECPU="3000"

# Security (Production-like)
export ENABLE_NAT_GATEWAY="true"
export ENABLE_CLOUDFRONT="true"
export ENABLE_WAF="true"
export CLOUDWATCH_RETENTION="7"  # 7 days
```

**Estimated Cost:** $250-350/month

---

### Production Environment

**File:** `parameters-prod.env`

```bash
# AWS Configuration
export AWS_ACCOUNT_ID="123456789012"
export AWS_REGION="us-east-1"

# Project Configuration
export PROJECT_NAME="spring-redis-app-prod"
export EXECUTOR_NAME="ops-team"
export ENVIRONMENT="production"

# ECS Configuration (Full)
export ECS_TASK_CPU="2048"     # 2 vCPU
export ECS_TASK_MEMORY="4096"  # 4 GB
export ECS_DESIRED_COUNT="3"   # 3 tasks
export ECS_MIN_CAPACITY="3"
export ECS_MAX_CAPACITY="10"

# Redis Configuration (Full)
export REDIS_MIN_STORAGE="2"
export REDIS_MAX_STORAGE="5"
export REDIS_MIN_ECPU="2000"
export REDIS_MAX_ECPU="5000"

# Security (Full)
export ENABLE_NAT_GATEWAY="true"
export ENABLE_CLOUDFRONT="true"
export ENABLE_WAF="true"
export CLOUDWATCH_RETENTION="30"  # 30 days

# Backup Configuration
export ENABLE_AUTOMATED_BACKUPS="true"
export BACKUP_RETENTION_DAYS="30"
```

**Estimated Cost:** $470-600/month

---

## Deployment Workflow

### 1. Deploy Development Environment

```bash
# Load dev parameters
cd /home/ial
source parameters-dev.env

# Verify parameters
echo "Deploying to: $PROJECT_NAME in $AWS_REGION"

# Deploy all phases
for phase in phases/*.yaml; do
  echo "Deploying $(basename $phase)..."
  # Read phase file
  cat $phase
  # Execute commands manually (following IaL principle)
  # Validate each resource
done
```

---

### 2. Deploy Staging Environment

```bash
# Load staging parameters
source parameters-staging.env

# Verify parameters
echo "Deploying to: $PROJECT_NAME in $AWS_REGION"

# Deploy all phases (same process as dev)
for phase in phases/*.yaml; do
  echo "Deploying $(basename $phase)..."
  cat $phase
  # Execute commands manually
done
```

---

### 3. Deploy Production Environment

```bash
# Load production parameters
source parameters-prod.env

# Verify parameters
echo "Deploying to: $PROJECT_NAME in $AWS_REGION"

# Deploy all phases with extra validation
for phase in phases/*.yaml; do
  echo "Deploying $(basename $phase)..."
  cat $phase
  # Execute commands manually
  # Extra validation for production
  # Verify each resource before proceeding
done
```

---

## Environment-Specific Configurations

### Development Optimizations

**Skip these phases in dev:**
- Phase 12: WAF & CloudFront (use ALB directly)
- Phase 13: VPC Flow Logs (optional)

**Modify these phases:**
- Phase 03: Use VPC endpoints instead of NAT Gateways
- Phase 08: Single task, smaller resources
- Phase 09: Disable auto scaling or set min=1, max=2
- Phase 11: Minimal Redis configuration

---

### Staging Considerations

**Same as production except:**
- Smaller task count (2 vs 3)
- Lower auto scaling limits (max 5 vs 10)
- Shorter log retention (7 vs 30 days)
- Can use smaller Redis limits

---

### Production Requirements

**Must include:**
- All 17 phases (including 05b)
- Full security services (GuardDuty, Security Hub, Config)
- WAF with rate limiting
- CloudFront with DDoS protection
- VPC Flow Logs
- 30-day log retention
- Automated backups
- Multi-AZ deployment

---

## GitHub Actions Configuration

### Development Workflow

**File:** `.github/workflows/deploy-dev.yml`

```yaml
name: Deploy to Development

on:
  push:
    branches: [develop]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: spring-redis-app-dev
  ECS_CLUSTER: spring-redis-app-dev-cluster
  ECS_SERVICE: spring-redis-app-dev-service
  TASK_FAMILY: spring-redis-app-dev-task

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/spring-redis-app-dev-github-actions-role
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Build and push Docker image
        run: |
          # Build with Bedrock validation
          docker build --target validator -t validator .
          docker build -t ${{ env.ECR_REPOSITORY }}:latest .
          
          # Push to ECR
          aws ecr get-login-password | docker login --username AWS --password-stdin ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${{ env.AWS_REGION }}.amazonaws.com
          docker tag ${{ env.ECR_REPOSITORY }}:latest ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${{ env.AWS_REGION }}.amazonaws.com/${{ env.ECR_REPOSITORY }}:latest
          docker push ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${{ env.AWS_REGION }}.amazonaws.com/${{ env.ECR_REPOSITORY }}:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster ${{ env.ECS_CLUSTER }} --service ${{ env.ECS_SERVICE }} --force-new-deployment
```

---

### Staging Workflow

**File:** `.github/workflows/deploy-staging.yml`

```yaml
name: Deploy to Staging

on:
  push:
    branches: [staging]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: spring-redis-app-staging
  ECS_CLUSTER: spring-redis-app-staging-cluster
  ECS_SERVICE: spring-redis-app-staging-service
  TASK_FAMILY: spring-redis-app-staging-task

# Same steps as dev, different environment variables
```

---

### Production Workflow

**File:** `.github/workflows/deploy-prod.yml`

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: spring-redis-app-prod
  ECS_CLUSTER: spring-redis-app-prod-cluster
  ECS_SERVICE: spring-redis-app-prod-service
  TASK_FAMILY: spring-redis-app-prod-task

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    steps:
      # Same as staging with additional validations
      
      - name: Run integration tests
        run: |
          # Run tests before deployment
          ./run-integration-tests.sh
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster ${{ env.ECS_CLUSTER }} --service ${{ env.ECS_SERVICE }} --force-new-deployment
      
      - name: Wait for deployment
        run: |
          aws ecs wait services-stable --cluster ${{ env.ECS_CLUSTER }} --services ${{ env.ECS_SERVICE }}
      
      - name: Verify deployment
        run: |
          # Health check
          curl -f https://api.example.com/actuator/health
```

---

## Environment Isolation

### Network Isolation

Each environment has its own VPC:
- Dev: 10.0.0.0/16
- Staging: 10.1.0.0/16
- Production: 10.2.0.0/16

### IAM Isolation

Separate IAM roles per environment:
- `spring-redis-app-dev-ecs-task-role`
- `spring-redis-app-staging-ecs-task-role`
- `spring-redis-app-prod-ecs-task-role`

### Resource Tagging

All resources tagged with environment:
```bash
--tags Key=Environment,Value=dev
--tags Key=Environment,Value=staging
--tags Key=Environment,Value=production
```

---

## Cost Comparison

| Environment | Monthly Cost | Use Case |
|-------------|-------------|----------|
| Development | $80-120 | Feature development, testing |
| Staging | $250-350 | Pre-production validation |
| Production | $470-600 | Live customer traffic |
| **Total** | **$800-1,070** | All environments |

---

## Promotion Workflow

### Dev → Staging

```bash
# 1. Test in dev
# 2. Merge develop → staging branch
# 3. GitHub Actions deploys to staging
# 4. Run integration tests
# 5. Manual QA validation
```

### Staging → Production

```bash
# 1. Test in staging
# 2. Create release tag: v1.0.0
# 3. Merge staging → main branch
# 4. GitHub Actions requires manual approval
# 5. Deploy to production
# 6. Monitor for 24 hours
```

---

## Rollback Strategy

See [rollback-strategy.md](rollback-strategy.md) for detailed rollback procedures.

---

## Best Practices

1. **Always deploy to dev first**
2. **Test in staging before production**
3. **Use feature flags for risky changes**
4. **Monitor each environment separately**
5. **Keep staging as close to production as possible**
6. **Use different AWS accounts for production isolation** (recommended)
7. **Automate dev/staging, manual approval for production**
8. **Tag all resources with environment name**
9. **Use separate parameter files per environment**
10. **Document environment-specific configurations**

---

## Next Steps

- Review [multi-region.md](multi-region.md) for multi-region deployment
- Check [rollback-strategy.md](rollback-strategy.md) for rollback procedures
- See [cost-optimization.md](../docs/cost-optimization.md) for cost reduction strategies
