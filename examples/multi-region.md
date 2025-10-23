# Multi-Region Deployment Example

Deploy the application across multiple AWS regions for disaster recovery and global reach.

## Overview

This example demonstrates deploying to multiple regions:

- **Primary Region:** us-east-1 (N. Virginia)
- **Secondary Region:** us-west-2 (Oregon)
- **Tertiary Region:** eu-west-1 (Ireland) - Optional

---

## Architecture

```
                    ┌─────────────────┐
                    │  Route 53 DNS   │
                    │  Health Checks  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         us-east-1      us-west-2      eu-west-1
              │              │              │
    ┌─────────▼─────────┐   │   ┌──────────▼──────────┐
    │   CloudFront      │   │   │   CloudFront        │
    │   + WAF           │   │   │   + WAF             │
    └─────────┬─────────┘   │   └──────────┬──────────┘
              │              │              │
    ┌─────────▼─────────┐   │   ┌──────────▼──────────┐
    │   ALB             │   │   │   ALB               │
    └─────────┬─────────┘   │   └──────────┬──────────┘
              │              │              │
    ┌─────────▼─────────┐   │   ┌──────────▼──────────┐
    │   ECS Fargate     │   │   │   ECS Fargate       │
    │   (2-10 tasks)    │   │   │   (2-10 tasks)      │
    └─────────┬─────────┘   │   └──────────┬──────────┘
              │              │              │
    ┌─────────▼─────────┐   │   ┌──────────▼──────────┐
    │   Redis Global    │◄──┴──►│   Redis Global      │
    │   Datastore       │        │   Datastore         │
    └───────────────────┘        └─────────────────────┘
```

---

## Region Configurations

### Primary Region (us-east-1)

**File:** `parameters-us-east-1.env`

```bash
# AWS Configuration
export AWS_ACCOUNT_ID="123456789012"
export AWS_REGION="us-east-1"

# Project Configuration
export PROJECT_NAME="spring-redis-app"
export EXECUTOR_NAME="ops-team"
export ENVIRONMENT="production"
export REGION_TYPE="primary"

# ECS Configuration
export ECS_TASK_CPU="2048"
export ECS_TASK_MEMORY="4096"
export ECS_DESIRED_COUNT="3"
export ECS_MIN_CAPACITY="3"
export ECS_MAX_CAPACITY="10"

# Redis Configuration (Primary)
export REDIS_MIN_STORAGE="2"
export REDIS_MAX_STORAGE="5"
export REDIS_MIN_ECPU="2000"
export REDIS_MAX_ECPU="5000"
export REDIS_REPLICATION="enabled"

# Route 53
export ROUTE53_ZONE_ID="Z1234567890ABC"
export ROUTE53_RECORD_NAME="api.example.com"
export ROUTE53_WEIGHT="100"  # Primary receives most traffic
```

---

### Secondary Region (us-west-2)

**File:** `parameters-us-west-2.env`

```bash
# AWS Configuration
export AWS_ACCOUNT_ID="123456789012"
export AWS_REGION="us-west-2"

# Project Configuration
export PROJECT_NAME="spring-redis-app"
export EXECUTOR_NAME="ops-team"
export ENVIRONMENT="production"
export REGION_TYPE="secondary"

# ECS Configuration (Same as primary)
export ECS_TASK_CPU="2048"
export ECS_TASK_MEMORY="4096"
export ECS_DESIRED_COUNT="2"  # Slightly fewer tasks
export ECS_MIN_CAPACITY="2"
export ECS_MAX_CAPACITY="8"

# Redis Configuration (Replica)
export REDIS_MIN_STORAGE="2"
export REDIS_MAX_STORAGE="5"
export REDIS_MIN_ECPU="2000"
export REDIS_MAX_ECPU="5000"
export REDIS_REPLICATION="enabled"

# Route 53
export ROUTE53_ZONE_ID="Z1234567890ABC"
export ROUTE53_RECORD_NAME="api.example.com"
export ROUTE53_WEIGHT="50"  # Secondary receives less traffic
```

---

## Deployment Steps

### 1. Deploy Primary Region (us-east-1)

```bash
# Load primary region parameters
cd /home/ial
source parameters-us-east-1.env

# Deploy all phases
echo "Deploying to PRIMARY region: $AWS_REGION"

# Phase 00: DynamoDB State
aws dynamodb create-table \
  --table-name ${PROJECT_NAME}-ial-state \
  --attribute-definitions AttributeName=PhaseId,AttributeType=S \
  --key-schema AttributeName=PhaseId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ${AWS_REGION}

# Continue with all phases...
# Phase 01-15 (same as single-region deployment)
```

---

### 2. Deploy Secondary Region (us-west-2)

```bash
# Load secondary region parameters
source parameters-us-west-2.env

# Deploy all phases
echo "Deploying to SECONDARY region: $AWS_REGION"

# Deploy same phases as primary
# Resources will be created in us-west-2
```

---

### 3. Configure Redis Global Datastore

**Primary Region (us-east-1):**

```bash
# Create primary Redis cluster
aws elasticache create-serverless-cache \
  --serverless-cache-name ${PROJECT_NAME}-redis-primary \
  --engine redis \
  --major-engine-version 7 \
  --region us-east-1

# Create Global Datastore
aws elasticache create-global-replication-group \
  --global-replication-group-id-suffix ${PROJECT_NAME}-global \
  --primary-replication-group-id ${PROJECT_NAME}-redis-primary \
  --global-replication-group-description "Global Redis for ${PROJECT_NAME}" \
  --region us-east-1
```

**Secondary Region (us-west-2):**

```bash
# Add secondary region to Global Datastore
aws elasticache create-replication-group \
  --replication-group-id ${PROJECT_NAME}-redis-secondary \
  --replication-group-description "Secondary Redis for ${PROJECT_NAME}" \
  --global-replication-group-id ${PROJECT_NAME}-global \
  --region us-west-2
```

**Note:** Redis Serverless doesn't support Global Datastore yet. Use Redis Cluster mode for multi-region replication.

---

### 4. Configure Route 53 for Multi-Region

**Create Health Checks:**

```bash
# Health check for us-east-1
aws route53 create-health-check \
  --caller-reference $(date +%s)-us-east-1 \
  --health-check-config \
    IPAddress=${ALB_IP_US_EAST_1},Port=443,Type=HTTPS,ResourcePath=/actuator/health,FullyQualifiedDomainName=api-us-east-1.example.com

export HEALTH_CHECK_US_EAST_1="<health-check-id>"

# Health check for us-west-2
aws route53 create-health-check \
  --caller-reference $(date +%s)-us-west-2 \
  --health-check-config \
    IPAddress=${ALB_IP_US_WEST_2},Port=443,Type=HTTPS,ResourcePath=/actuator/health,FullyQualifiedDomainName=api-us-west-2.example.com

export HEALTH_CHECK_US_WEST_2="<health-check-id>"
```

**Create Weighted Routing Policy:**

```bash
# Primary region record (70% traffic)
aws route53 change-resource-record-sets \
  --hosted-zone-id ${ROUTE53_ZONE_ID} \
  --change-batch file://<(cat <<EOF
{
  "Changes": [{
    "Action": "CREATE",
    "ResourceRecordSet": {
      "Name": "api.example.com",
      "Type": "A",
      "SetIdentifier": "us-east-1",
      "Weight": 70,
      "HealthCheckId": "${HEALTH_CHECK_US_EAST_1}",
      "AliasTarget": {
        "HostedZoneId": "${ALB_HOSTED_ZONE_ID}",
        "DNSName": "${ALB_DNS_US_EAST_1}",
        "EvaluateTargetHealth": true
      }
    }
  }]
}
EOF
)

# Secondary region record (30% traffic)
aws route53 change-resource-record-sets \
  --hosted-zone-id ${ROUTE53_ZONE_ID} \
  --change-batch file://<(cat <<EOF
{
  "Changes": [{
    "Action": "CREATE",
    "ResourceRecordSet": {
      "Name": "api.example.com",
      "Type": "A",
      "SetIdentifier": "us-west-2",
      "Weight": 30,
      "HealthCheckId": "${HEALTH_CHECK_US_WEST_2}",
      "AliasTarget": {
        "HostedZoneId": "${ALB_HOSTED_ZONE_ID}",
        "DNSName": "${ALB_DNS_US_WEST_2}",
        "EvaluateTargetHealth": true
      }
    }
  }]
}
EOF
)
```

---

## Failover Strategy

### Automatic Failover

Route 53 health checks automatically route traffic away from unhealthy regions:

1. Health check fails in us-east-1
2. Route 53 stops routing traffic to us-east-1
3. All traffic goes to us-west-2
4. When us-east-1 recovers, traffic gradually returns

---

### Manual Failover

**Scenario:** Planned maintenance in us-east-1

```bash
# 1. Reduce weight for us-east-1 to 0
aws route53 change-resource-record-sets \
  --hosted-zone-id ${ROUTE53_ZONE_ID} \
  --change-batch file://<(cat <<EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "api.example.com",
      "Type": "A",
      "SetIdentifier": "us-east-1",
      "Weight": 0,
      "HealthCheckId": "${HEALTH_CHECK_US_EAST_1}",
      "AliasTarget": {
        "HostedZoneId": "${ALB_HOSTED_ZONE_ID}",
        "DNSName": "${ALB_DNS_US_EAST_1}",
        "EvaluateTargetHealth": true
      }
    }
  }]
}
EOF
)

# 2. Wait 5 minutes for DNS propagation

# 3. Perform maintenance in us-east-1

# 4. Restore weight to 70
aws route53 change-resource-record-sets \
  --hosted-zone-id ${ROUTE53_ZONE_ID} \
  --change-batch file://<(cat <<EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "api.example.com",
      "Type": "A",
      "SetIdentifier": "us-east-1",
      "Weight": 70,
      "HealthCheckId": "${HEALTH_CHECK_US_EAST_1}",
      "AliasTarget": {
        "HostedZoneId": "${ALB_HOSTED_ZONE_ID}",
        "DNSName": "${ALB_DNS_US_EAST_1}",
        "EvaluateTargetHealth": true
      }
    }
  }]
}
EOF
)
```

---

## Data Replication

### Redis Global Datastore

- **Replication Lag:** < 1 second
- **Consistency:** Eventual consistency
- **Failover:** Automatic promotion of secondary to primary

**Monitor Replication:**

```bash
# Check replication lag
aws cloudwatch get-metric-statistics \
  --namespace AWS/ElastiCache \
  --metric-name ReplicationLag \
  --dimensions Name=GlobalDatastoreId,Value=${PROJECT_NAME}-global \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --region us-east-1
```

---

### Application State

For stateless applications (like this Spring Boot app):
- No application state to replicate
- All state in Redis (replicated globally)
- Sessions stored in Redis (available in all regions)

---

## Cost Considerations

### Multi-Region Costs

| Component | Single Region | Multi-Region (2) | Increase |
|-----------|--------------|------------------|----------|
| ECS Fargate | $180 | $360 | +100% |
| Redis | $120 | $240 | +100% |
| ALB | $25 | $50 | +100% |
| CloudFront | $50 | $50 | 0% (global) |
| NAT Gateway | $32 | $64 | +100% |
| Data Transfer | $20 | $60 | +200% |
| Route 53 | $5 | $10 | +100% |
| **Total** | **$470** | **$884** | **+88%** |

**Cost Optimization:**
- Use smaller task counts in secondary region
- Enable auto scaling to scale down during low traffic
- Use VPC endpoints to reduce data transfer costs

---

## Monitoring Multi-Region

### CloudWatch Dashboard

Create unified dashboard showing all regions:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name ${PROJECT_NAME}-multi-region \
  --dashboard-body file://<(cat <<EOF
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ECS", "CPUUtilization", {"region": "us-east-1", "stat": "Average"}],
          ["...", {"region": "us-west-2", "stat": "Average"}]
        ],
        "title": "ECS CPU Utilization - All Regions",
        "region": "us-east-1"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ApplicationELB", "TargetResponseTime", {"region": "us-east-1"}],
          ["...", {"region": "us-west-2"}]
        ],
        "title": "ALB Response Time - All Regions",
        "region": "us-east-1"
      }
    }
  ]
}
EOF
)
```

---

### Route 53 Health Check Monitoring

```bash
# Create CloudWatch alarm for health check failures
aws cloudwatch put-metric-alarm \
  --alarm-name ${PROJECT_NAME}-us-east-1-health \
  --alarm-description "Alert when us-east-1 health check fails" \
  --metric-name HealthCheckStatus \
  --namespace AWS/Route53 \
  --statistic Minimum \
  --period 60 \
  --evaluation-periods 2 \
  --threshold 1 \
  --comparison-operator LessThanThreshold \
  --dimensions Name=HealthCheckId,Value=${HEALTH_CHECK_US_EAST_1} \
  --alarm-actions ${SNS_TOPIC_ARN} \
  --region us-east-1
```

---

## Disaster Recovery

### RTO and RPO

- **RTO (Recovery Time Objective):** < 5 minutes (automatic failover)
- **RPO (Recovery Point Objective):** < 1 second (Redis replication lag)

### DR Testing

**Monthly DR Test:**

```bash
# 1. Simulate us-east-1 failure
aws route53 change-resource-record-sets \
  --hosted-zone-id ${ROUTE53_ZONE_ID} \
  --change-batch '{"Changes":[{"Action":"UPSERT","ResourceRecordSet":{"Name":"api.example.com","Type":"A","SetIdentifier":"us-east-1","Weight":0}}]}'

# 2. Verify traffic shifts to us-west-2
# Monitor CloudWatch metrics

# 3. Verify application functionality
curl https://api.example.com/actuator/health

# 4. Restore us-east-1
aws route53 change-resource-record-sets \
  --hosted-zone-id ${ROUTE53_ZONE_ID} \
  --change-batch '{"Changes":[{"Action":"UPSERT","ResourceRecordSet":{"Name":"api.example.com","Type":"A","SetIdentifier":"us-east-1","Weight":70}}]}'

# 5. Document results
```

---

## Best Practices

1. **Deploy to primary region first, validate, then deploy to secondary**
2. **Use identical configurations across regions** (except region-specific values)
3. **Test failover monthly**
4. **Monitor replication lag continuously**
5. **Use Route 53 health checks for automatic failover**
6. **Keep secondary region warm** (always running, not cold standby)
7. **Use CloudWatch cross-region dashboards**
8. **Document failover procedures**
9. **Practice manual failover quarterly**
10. **Consider latency-based routing for global users**

---

## Latency-Based Routing (Optional)

For global users, use latency-based routing instead of weighted:

```bash
# Primary region (latency-based)
aws route53 change-resource-record-sets \
  --hosted-zone-id ${ROUTE53_ZONE_ID} \
  --change-batch file://<(cat <<EOF
{
  "Changes": [{
    "Action": "CREATE",
    "ResourceRecordSet": {
      "Name": "api.example.com",
      "Type": "A",
      "SetIdentifier": "us-east-1",
      "Region": "us-east-1",
      "HealthCheckId": "${HEALTH_CHECK_US_EAST_1}",
      "AliasTarget": {
        "HostedZoneId": "${ALB_HOSTED_ZONE_ID}",
        "DNSName": "${ALB_DNS_US_EAST_1}",
        "EvaluateTargetHealth": true
      }
    }
  }]
}
EOF
)

# Secondary region (latency-based)
aws route53 change-resource-record-sets \
  --hosted-zone-id ${ROUTE53_ZONE_ID} \
  --change-batch file://<(cat <<EOF
{
  "Changes": [{
    "Action": "CREATE",
    "ResourceRecordSet": {
      "Name": "api.example.com",
      "Type": "A",
      "SetIdentifier": "us-west-2",
      "Region": "us-west-2",
      "HealthCheckId": "${HEALTH_CHECK_US_WEST_2}",
      "AliasTarget": {
        "HostedZoneId": "${ALB_HOSTED_ZONE_ID}",
        "DNSName": "${ALB_DNS_US_WEST_2}",
        "EvaluateTargetHealth": true
      }
    }
  }]
}
EOF
)
```

Users will be automatically routed to the nearest region with lowest latency.

---

## Next Steps

- Review [multi-environment.md](multi-environment.md) for environment-specific configurations
- Check [rollback-strategy.md](rollback-strategy.md) for rollback procedures
- See [../docs/cost-optimization.md](../docs/cost-optimization.md) for multi-region cost optimization
