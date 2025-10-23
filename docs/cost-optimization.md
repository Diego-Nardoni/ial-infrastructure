# Cost Optimization Guide

Strategies to reduce AWS costs while maintaining performance and reliability.

## Current Cost Breakdown

**Monthly Estimate: ~$470**

| Service | Monthly Cost | Optimization Potential |
|---------|-------------|----------------------|
| ECS Fargate | $180 | High (40-60% savings) |
| Redis Serverless | $120 | Medium (20-30% savings) |
| ALB | $25 | Low (10-20% savings) |
| CloudFront | $50 | Medium (30-50% savings) |
| NAT Gateway | $32 | High (50-90% savings) |
| VPC Endpoints | $28 | N/A (cost optimization tool) |
| CloudWatch | $15 | Medium (20-40% savings) |
| KMS | $9 | Low (minimal) |
| Other | $11 | Low (minimal) |

**Potential Savings: $150-250/month (32-53%)**

---

## High-Impact Optimizations

### 1. Replace NAT Gateways with VPC Endpoints

**Current Cost:** $32/month (2 NAT Gateways)
**Optimized Cost:** $7-14/month (VPC Endpoints)
**Savings:** $18-25/month (56-78%)

**Implementation:**

```bash
# Create VPC endpoints for AWS services
# S3 Gateway Endpoint (Free)
aws ec2 create-vpc-endpoint \
  --vpc-id ${VPC_ID} \
  --service-name com.amazonaws.${AWS_REGION}.s3 \
  --route-table-ids ${PRIVATE_RT_1} ${PRIVATE_RT_2} \
  --region ${AWS_REGION}

# ECR API Interface Endpoint ($7/month)
aws ec2 create-vpc-endpoint \
  --vpc-id ${VPC_ID} \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.${AWS_REGION}.ecr.api \
  --subnet-ids ${PRIVATE_SUBNET_1} ${PRIVATE_SUBNET_2} \
  --security-group-ids ${VPC_ENDPOINT_SG} \
  --region ${AWS_REGION}

# ECR DKR Interface Endpoint ($7/month)
aws ec2 create-vpc-endpoint \
  --vpc-id ${VPC_ID} \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.${AWS_REGION}.ecr.dkr \
  --subnet-ids ${PRIVATE_SUBNET_1} ${PRIVATE_SUBNET_2} \
  --security-group-ids ${VPC_ENDPOINT_SG} \
  --region ${AWS_REGION}

# CloudWatch Logs Interface Endpoint ($7/month)
aws ec2 create-vpc-endpoint \
  --vpc-id ${VPC_ID} \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.${AWS_REGION}.logs \
  --subnet-ids ${PRIVATE_SUBNET_1} ${PRIVATE_SUBNET_2} \
  --security-group-ids ${VPC_ENDPOINT_SG} \
  --region ${AWS_REGION}

# After VPC endpoints are working, delete NAT Gateways
aws ec2 delete-nat-gateway --nat-gateway-id ${NAT_GW_1} --region ${AWS_REGION}
aws ec2 delete-nat-gateway --nat-gateway-id ${NAT_GW_2} --region ${AWS_REGION}

# Release Elastic IPs
aws ec2 release-address --allocation-id ${EIP_1} --region ${AWS_REGION}
aws ec2 release-address --allocation-id ${EIP_2} --region ${AWS_REGION}
```

**Trade-offs:**
- VPC endpoints only work for AWS services
- Internet access requires NAT Gateway or proxy
- For this application (ECS + Redis + AWS services), VPC endpoints are sufficient

---

### 2. Right-Size ECS Fargate Tasks

**Current Cost:** $180/month (2 tasks, 2 vCPU, 4GB RAM each)
**Optimized Cost:** $90-108/month (2 tasks, 1 vCPU, 2GB RAM each)
**Savings:** $72-90/month (40-50%)

**Implementation:**

```bash
# Monitor current resource usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=${PROJECT_NAME}-service Name=ClusterName,Value=${PROJECT_NAME}-cluster \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average,Maximum \
  --region ${AWS_REGION}

# If average CPU < 30% and max < 60%, reduce to 1 vCPU, 2GB RAM
# Edit phases/08-ecs-task-service.yaml
# Change: cpu: "1024" (1 vCPU), memory: "2048" (2GB)

# Register new task definition
aws ecs register-task-definition --cli-input-json file://task-definition-optimized.json

# Update service
aws ecs update-service \
  --cluster ${PROJECT_NAME}-cluster \
  --service ${PROJECT_NAME}-service \
  --task-definition ${PROJECT_NAME}-task:2 \
  --region ${AWS_REGION}
```

**Monitoring:**
- Watch CPU/Memory metrics for 1 week
- Ensure no OOM errors
- Verify response times remain acceptable

---

### 3. Optimize Redis Serverless Configuration

**Current Cost:** $120/month (1-5GB storage, auto-scaling ECPU)
**Optimized Cost:** $84-96/month (1-3GB storage, lower ECPU limits)
**Savings:** $24-36/month (20-30%)

**Implementation:**

```bash
# Monitor Redis usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/ElastiCache \
  --metric-name ElastiCacheProcessingUnits \
  --dimensions Name=ServerlessCacheName,Value=${PROJECT_NAME}-redis \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average,Maximum \
  --region ${AWS_REGION}

# If usage is consistently low, reduce limits
aws elasticache modify-serverless-cache \
  --serverless-cache-name ${PROJECT_NAME}-redis \
  --cache-usage-limits DataStorage={Maximum=3,Minimum=1,Unit=GB},ECPUPerSecond={Maximum=3000,Minimum=1000} \
  --region ${AWS_REGION}
```

**Alternative: Switch to Redis Cluster Mode**

For predictable workloads, consider Redis Cluster:
- cache.t4g.micro: $12/month (0.5GB)
- cache.t4g.small: $24/month (1.5GB)
- Savings: $96-108/month (80-90%)

---

### 4. Optimize CloudFront Caching

**Current Cost:** $50/month (data transfer + requests)
**Optimized Cost:** $25-35/month (improved cache hit ratio)
**Savings:** $15-25/month (30-50%)

**Implementation:**

```bash
# Update CloudFront cache behavior
aws cloudfront get-distribution-config --id ${CLOUDFRONT_ID} > distribution-config.json

# Edit distribution-config.json:
# - Increase DefaultTTL from 86400 to 604800 (7 days) for static content
# - Enable compression
# - Add cache policy for API responses

aws cloudfront update-distribution --id ${CLOUDFRONT_ID} --if-match ${ETAG} --distribution-config file://distribution-config.json

# Monitor cache hit ratio
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name CacheHitRate \
  --dimensions Name=DistributionId,Value=${CLOUDFRONT_ID} \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average \
  --region us-east-1
```

**Target:** Cache hit ratio > 80%

---

### 5. Reduce CloudWatch Logs Retention

**Current Cost:** $15/month (30-day retention)
**Optimized Cost:** $6-9/month (7-day retention)
**Savings:** $6-9/month (40-60%)

**Implementation:**

```bash
# List log groups
aws logs describe-log-groups --region ${AWS_REGION}

# Update retention for application logs
aws logs put-retention-policy \
  --log-group-name /ecs/${PROJECT_NAME} \
  --retention-in-days 7 \
  --region ${AWS_REGION}

# Update retention for VPC Flow Logs
aws logs put-retention-policy \
  --log-group-name /aws/vpc/${PROJECT_NAME} \
  --retention-in-days 7 \
  --region ${AWS_REGION}

# For compliance, export to S3 before reducing retention
aws logs create-export-task \
  --log-group-name /ecs/${PROJECT_NAME} \
  --from $(date -u -d '30 days ago' +%s)000 \
  --to $(date -u +%s)000 \
  --destination ${PROJECT_NAME}-logs-archive \
  --region ${AWS_REGION}
```

---

### 6. Optimize ECS Auto Scaling

**Current Cost:** Included in ECS Fargate cost
**Optimization:** Reduce minimum task count during off-peak hours

**Implementation:**

```bash
# Create scheduled scaling for off-peak hours (e.g., 10 PM - 6 AM)
aws application-autoscaling put-scheduled-action \
  --service-namespace ecs \
  --resource-id service/${PROJECT_NAME}-cluster/${PROJECT_NAME}-service \
  --scheduled-action-name scale-down-night \
  --schedule "cron(0 22 * * ? *)" \
  --scalable-target-action MinCapacity=1,MaxCapacity=5 \
  --region ${AWS_REGION}

# Scale back up during business hours
aws application-autoscaling put-scheduled-action \
  --service-namespace ecs \
  --resource-id service/${PROJECT_NAME}-cluster/${PROJECT_NAME}-service \
  --scheduled-action-name scale-up-morning \
  --schedule "cron(0 6 * * ? *)" \
  --scalable-target-action MinCapacity=2,MaxCapacity=10 \
  --region ${AWS_REGION}
```

**Savings:** $36-54/month (20-30% of ECS cost)

---

### 7. Use Savings Plans or Reserved Instances

**Current Cost:** On-demand pricing
**Optimized Cost:** 30-50% discount with 1-year commitment

**Implementation:**

```bash
# Calculate Fargate usage
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '3 months ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://<(echo '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Elastic Container Service"]}}') \
  --region ${AWS_REGION}

# Purchase Compute Savings Plan (recommended)
# Go to AWS Console > Billing > Savings Plans
# Select Compute Savings Plan
# Commit to $50-100/month for 1 year
# Expected savings: $18-36/month (30-50% of ECS cost)
```

---

## Medium-Impact Optimizations

### 8. Optimize ALB Configuration

**Savings:** $2-5/month

```bash
# Enable connection draining to reduce idle connections
aws elbv2 modify-target-group-attributes \
  --target-group-arn ${TARGET_GROUP_ARN} \
  --attributes Key=deregistration_delay.timeout_seconds,Value=30 \
  --region ${AWS_REGION}

# Enable HTTP/2 for better performance
aws elbv2 modify-load-balancer-attributes \
  --load-balancer-arn ${ALB_ARN} \
  --attributes Key=routing.http2.enabled,Value=true \
  --region ${AWS_REGION}
```

---

### 9. Optimize KMS Key Usage

**Savings:** $1-2/month

```bash
# Use single KMS key for multiple services instead of 3 separate keys
# Consolidate ECS, Redis, and Logs encryption to one key
# Savings: $6/month (2 fewer keys)

# Note: Evaluate security requirements before consolidating
```

---

### 10. Enable S3 Intelligent-Tiering for Logs

**Savings:** $3-8/month

```bash
# Create S3 bucket for log archives
aws s3api create-bucket \
  --bucket ${PROJECT_NAME}-logs-archive \
  --region ${AWS_REGION}

# Enable Intelligent-Tiering
aws s3api put-bucket-intelligent-tiering-configuration \
  --bucket ${PROJECT_NAME}-logs-archive \
  --id LogsArchive \
  --intelligent-tiering-configuration file://<(cat <<EOF
{
  "Id": "LogsArchive",
  "Status": "Enabled",
  "Tierings": [
    {
      "Days": 90,
      "AccessTier": "ARCHIVE_ACCESS"
    },
    {
      "Days": 180,
      "AccessTier": "DEEP_ARCHIVE_ACCESS"
    }
  ]
}
EOF
)

# Export CloudWatch Logs to S3
aws logs create-export-task \
  --log-group-name /ecs/${PROJECT_NAME} \
  --from $(date -u -d '30 days ago' +%s)000 \
  --to $(date -u +%s)000 \
  --destination ${PROJECT_NAME}-logs-archive \
  --region ${AWS_REGION}
```

---

## Cost Monitoring

### Set Up Budget Alerts

```bash
# Create budget
aws budgets create-budget \
  --account-id ${AWS_ACCOUNT_ID} \
  --budget file://<(cat <<EOF
{
  "BudgetName": "${PROJECT_NAME}-monthly-budget",
  "BudgetLimit": {
    "Amount": "500",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
EOF
)

# Create alert at 80% threshold
aws budgets create-notification \
  --account-id ${AWS_ACCOUNT_ID} \
  --budget-name ${PROJECT_NAME}-monthly-budget \
  --notification NotificationType=ACTUAL,ComparisonOperator=GREATER_THAN,Threshold=80,ThresholdType=PERCENTAGE \
  --subscribers SubscriptionType=EMAIL,Address=your-email@example.com
```

---

### Enable Cost Anomaly Detection

```bash
# Create cost anomaly monitor
aws ce create-anomaly-monitor \
  --anomaly-monitor file://<(cat <<EOF
{
  "MonitorName": "${PROJECT_NAME}-cost-monitor",
  "MonitorType": "DIMENSIONAL",
  "MonitorDimension": "SERVICE"
}
EOF
)

# Create subscription for alerts
aws ce create-anomaly-subscription \
  --anomaly-subscription file://<(cat <<EOF
{
  "SubscriptionName": "${PROJECT_NAME}-cost-alerts",
  "Threshold": 100,
  "Frequency": "DAILY",
  "MonitorArnList": ["<monitor-arn>"],
  "Subscribers": [
    {
      "Type": "EMAIL",
      "Address": "your-email@example.com"
    }
  ]
}
EOF
)
```

---

## Optimization Summary

| Optimization | Effort | Savings/Month | Priority |
|--------------|--------|---------------|----------|
| VPC Endpoints | Medium | $18-25 | High |
| Right-size ECS | Low | $72-90 | High |
| Optimize Redis | Low | $24-36 | High |
| CloudFront Cache | Medium | $15-25 | Medium |
| Logs Retention | Low | $6-9 | Medium |
| Scheduled Scaling | Medium | $36-54 | Medium |
| Savings Plans | Low | $18-36 | High |
| ALB Optimization | Low | $2-5 | Low |
| KMS Consolidation | Medium | $6 | Low |
| S3 Tiering | Medium | $3-8 | Low |

**Total Potential Savings: $200-288/month (43-61%)**

**Optimized Monthly Cost: $182-270 (from $470)**

---

## Cost Optimization Checklist

- [ ] Replace NAT Gateways with VPC Endpoints
- [ ] Right-size ECS Fargate tasks (monitor for 1 week first)
- [ ] Optimize Redis Serverless limits
- [ ] Improve CloudFront cache hit ratio
- [ ] Reduce CloudWatch Logs retention to 7 days
- [ ] Implement scheduled ECS scaling for off-peak hours
- [ ] Purchase Compute Savings Plan (1-year commitment)
- [ ] Enable ALB connection draining
- [ ] Consolidate KMS keys (if security allows)
- [ ] Enable S3 Intelligent-Tiering for log archives
- [ ] Set up budget alerts at 80% threshold
- [ ] Enable Cost Anomaly Detection
- [ ] Review Cost Explorer monthly
- [ ] Tag all resources for cost allocation

---

## Next Steps

1. Start with high-priority, low-effort optimizations (right-sizing, logs retention)
2. Monitor impact for 1 week
3. Implement medium-priority optimizations (VPC endpoints, CloudFront)
4. Evaluate Savings Plans after 3 months of stable usage
5. Review costs monthly and adjust as needed
