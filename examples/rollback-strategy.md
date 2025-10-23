# Rollback Strategy

Comprehensive rollback procedures for the Spring Redis Application.

## Overview

This guide covers rollback strategies for:
- Application deployments
- Infrastructure changes
- Database migrations
- Configuration updates

---

## Application Rollback

### ECS Service Rollback

**Scenario:** New application version causing issues

**Quick Rollback (< 2 minutes):**

```bash
# 1. Get previous task definition
aws ecs describe-services \
  --cluster ${PROJECT_NAME}-cluster \
  --services ${PROJECT_NAME}-service \
  --query 'services[0].deployments' \
  --region ${AWS_REGION}

# 2. Identify previous stable revision
export PREVIOUS_TASK_DEF="${PROJECT_NAME}-task:5"  # Example: revision 5

# 3. Update service to previous task definition
aws ecs update-service \
  --cluster ${PROJECT_NAME}-cluster \
  --service ${PROJECT_NAME}-service \
  --task-definition ${PREVIOUS_TASK_DEF} \
  --force-new-deployment \
  --region ${AWS_REGION}

# 4. Monitor rollback
aws ecs wait services-stable \
  --cluster ${PROJECT_NAME}-cluster \
  --services ${PROJECT_NAME}-service \
  --region ${AWS_REGION}

# 5. Verify health
curl https://api.example.com/actuator/health
```

---

### Docker Image Rollback

**Scenario:** Need to rollback to specific Docker image

```bash
# 1. List available images
aws ecr describe-images \
  --repository-name ${PROJECT_NAME} \
  --query 'sort_by(imageDetails,&imagePushedAt)[-10:]' \
  --region ${AWS_REGION}

# 2. Identify previous stable image
export PREVIOUS_IMAGE_TAG="v1.2.3"  # Or commit SHA

# 3. Update task definition with previous image
aws ecs register-task-definition \
  --family ${PROJECT_NAME}-task \
  --container-definitions file://<(cat <<EOF
[{
  "name": "${PROJECT_NAME}",
  "image": "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}:${PREVIOUS_IMAGE_TAG}",
  "cpu": 2048,
  "memory": 4096,
  "essential": true,
  "portMappings": [{"containerPort": 8080, "protocol": "tcp"}]
}]
EOF
)

# 4. Update service
aws ecs update-service \
  --cluster ${PROJECT_NAME}-cluster \
  --service ${PROJECT_NAME}-service \
  --task-definition ${PROJECT_NAME}-task \
  --force-new-deployment \
  --region ${AWS_REGION}
```

---

## Infrastructure Rollback

### Phase-by-Phase Rollback

**General Principle:** Rollback in reverse order of deployment

**Rollback Order:**
1. Phase 15 → Phase 14 → ... → Phase 01 → Phase 00

**Example: Rollback Phase 10 (ALB)**

```bash
# 1. Identify resources to delete
cat phases/10-alb.yaml

# 2. Delete in reverse order
# Delete listener
aws elbv2 delete-listener --listener-arn ${LISTENER_ARN} --region ${AWS_REGION}

# Delete target group
aws elbv2 delete-target-group --target-group-arn ${TARGET_GROUP_ARN} --region ${AWS_REGION}

# Delete ALB
aws elbv2 delete-load-balancer --load-balancer-arn ${ALB_ARN} --region ${AWS_REGION}

# Wait for deletion
aws elbv2 wait load-balancers-deleted --load-balancer-arns ${ALB_ARN} --region ${AWS_REGION}

# Delete security group
aws ec2 delete-security-group --group-id ${ALB_SG} --region ${AWS_REGION}

# 3. Update DynamoDB state
aws dynamodb delete-item \
  --table-name ${PROJECT_NAME}-ial-state \
  --key '{"PhaseId":{"S":"10-alb"}}' \
  --region ${AWS_REGION}
```

---

### VPC Rollback

**Scenario:** Need to rollback VPC changes

```bash
# WARNING: This will delete all resources in the VPC
# Ensure all dependent resources are deleted first

# 1. Delete in order:
# - ECS services (Phase 08)
# - ALB (Phase 10)
# - Redis (Phase 11)
# - VPC endpoints
# - NAT Gateways
# - Internet Gateway
# - Subnets
# - Route tables
# - VPC

# 2. Example: Delete NAT Gateway
aws ec2 delete-nat-gateway --nat-gateway-id ${NAT_GW_1} --region ${AWS_REGION}
aws ec2 wait nat-gateway-deleted --nat-gateway-ids ${NAT_GW_1} --region ${AWS_REGION}

# 3. Release Elastic IP
aws ec2 release-address --allocation-id ${EIP_1} --region ${AWS_REGION}

# Continue with other resources...
```

---

## Configuration Rollback

### Parameter Store Rollback

**Scenario:** Incorrect parameter value deployed

```bash
# 1. Get parameter history
aws ssm get-parameter-history \
  --name "/${PROJECT_NAME}/redis/host" \
  --region ${AWS_REGION}

# 2. Identify previous value
export PREVIOUS_VALUE="redis-old-endpoint.cache.amazonaws.com"

# 3. Restore previous value
aws ssm put-parameter \
  --name "/${PROJECT_NAME}/redis/host" \
  --value "${PREVIOUS_VALUE}" \
  --type SecureString \
  --overwrite \
  --region ${AWS_REGION}

# 4. Restart ECS tasks to pick up new value
aws ecs update-service \
  --cluster ${PROJECT_NAME}-cluster \
  --service ${PROJECT_NAME}-service \
  --force-new-deployment \
  --region ${AWS_REGION}
```

---

### Environment Variable Rollback

**Scenario:** Incorrect environment variable in task definition

```bash
# 1. Get previous task definition
aws ecs describe-task-definition \
  --task-definition ${PROJECT_NAME}-task:5 \
  --query 'taskDefinition.containerDefinitions[0].environment' \
  --region ${AWS_REGION}

# 2. Register new task definition with corrected values
aws ecs register-task-definition \
  --family ${PROJECT_NAME}-task \
  --container-definitions file://task-definition-corrected.json

# 3. Update service
aws ecs update-service \
  --cluster ${PROJECT_NAME}-cluster \
  --service ${PROJECT_NAME}-service \
  --task-definition ${PROJECT_NAME}-task \
  --region ${AWS_REGION}
```

---

## Redis Rollback

### Redis Configuration Rollback

**Scenario:** Redis configuration change causing issues

```bash
# 1. Get previous configuration
aws elasticache describe-serverless-caches \
  --serverless-cache-name ${PROJECT_NAME}-redis \
  --region ${AWS_REGION}

# 2. Modify back to previous configuration
aws elasticache modify-serverless-cache \
  --serverless-cache-name ${PROJECT_NAME}-redis \
  --cache-usage-limits DataStorage={Maximum=5,Minimum=1,Unit=GB},ECPUPerSecond={Maximum=5000,Minimum=1000} \
  --region ${AWS_REGION}

# 3. Monitor status
aws elasticache describe-serverless-caches \
  --serverless-cache-name ${PROJECT_NAME}-redis \
  --query 'ServerlessCaches[0].Status' \
  --region ${AWS_REGION}
```

---

### Redis Data Rollback

**Scenario:** Data corruption or accidental deletion

```bash
# 1. List available snapshots
aws elasticache describe-serverless-cache-snapshots \
  --serverless-cache-name ${PROJECT_NAME}-redis \
  --region ${AWS_REGION}

# 2. Restore from snapshot
aws elasticache create-serverless-cache \
  --serverless-cache-name ${PROJECT_NAME}-redis-restored \
  --engine redis \
  --snapshot-arns-to-restore arn:aws:elasticache:${AWS_REGION}:${AWS_ACCOUNT_ID}:snapshot:${SNAPSHOT_NAME} \
  --region ${AWS_REGION}

# 3. Update Parameter Store with new endpoint
REDIS_ENDPOINT=$(aws elasticache describe-serverless-caches \
  --serverless-cache-name ${PROJECT_NAME}-redis-restored \
  --query 'ServerlessCaches[0].Endpoint.Address' \
  --output text \
  --region ${AWS_REGION})

aws ssm put-parameter \
  --name "/${PROJECT_NAME}/redis/host" \
  --value "${REDIS_ENDPOINT}" \
  --type SecureString \
  --overwrite \
  --region ${AWS_REGION}

# 4. Restart ECS tasks
aws ecs update-service \
  --cluster ${PROJECT_NAME}-cluster \
  --service ${PROJECT_NAME}-service \
  --force-new-deployment \
  --region ${AWS_REGION}
```

---

## GitHub Actions Rollback

### Revert Deployment

**Scenario:** GitHub Actions deployed bad version

```bash
# Option 1: Revert commit
git revert HEAD
git push origin main

# Option 2: Manual rollback (faster)
# Use ECS Service Rollback procedure above

# Option 3: Re-run previous successful workflow
# Go to GitHub Actions UI
# Find last successful deployment
# Click "Re-run all jobs"
```

---

## Multi-Region Rollback

### Rollback Single Region

```bash
# 1. Reduce Route 53 weight to 0 for affected region
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
      "Weight": 0
    }
  }]
}
EOF
)

# 2. Perform rollback in that region
# Use procedures above

# 3. Restore Route 53 weight
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
      "Weight": 70
    }
  }]
}
EOF
)
```

---

## Rollback Checklist

### Pre-Rollback

- [ ] Identify root cause of issue
- [ ] Determine rollback scope (app, infra, config)
- [ ] Identify previous stable version
- [ ] Notify stakeholders
- [ ] Take snapshot/backup if possible
- [ ] Document current state

### During Rollback

- [ ] Execute rollback procedure
- [ ] Monitor CloudWatch metrics
- [ ] Check application health
- [ ] Verify functionality
- [ ] Monitor error rates

### Post-Rollback

- [ ] Verify system stability
- [ ] Document rollback actions
- [ ] Analyze root cause
- [ ] Update runbooks
- [ ] Plan fix for original issue
- [ ] Notify stakeholders of completion

---

## Emergency Procedures

### Complete System Rollback

**Scenario:** Critical failure, need to rollback everything

```bash
# 1. Stop all traffic
aws route53 change-resource-record-sets \
  --hosted-zone-id ${ROUTE53_ZONE_ID} \
  --change-batch '{"Changes":[{"Action":"DELETE","ResourceRecordSet":{"Name":"api.example.com","Type":"A"}}]}'

# 2. Scale ECS to 0
aws ecs update-service \
  --cluster ${PROJECT_NAME}-cluster \
  --service ${PROJECT_NAME}-service \
  --desired-count 0 \
  --region ${AWS_REGION}

# 3. Restore from last known good state
# Use phase-by-phase rollback procedures

# 4. Verify in isolated environment

# 5. Gradually restore traffic
```

---

## Rollback Testing

### Monthly Rollback Drill

```bash
# 1. Deploy test version
# 2. Perform rollback
# 3. Measure rollback time
# 4. Document issues
# 5. Update procedures
```

**Target RTO:** < 5 minutes for application rollback

---

## Best Practices

1. **Always have a rollback plan before deploying**
2. **Test rollback procedures regularly**
3. **Keep previous 10 task definitions**
4. **Maintain 30 days of Docker images**
5. **Enable automated snapshots for Redis**
6. **Use blue/green deployments for zero-downtime**
7. **Monitor metrics during and after rollback**
8. **Document every rollback with root cause**
9. **Practice rollback drills monthly**
10. **Keep rollback procedures up to date**

---

## Rollback Decision Matrix

| Issue Severity | Response Time | Rollback Type |
|---------------|---------------|---------------|
| Critical (P0) | < 5 min | Immediate app rollback |
| High (P1) | < 15 min | App rollback + investigation |
| Medium (P2) | < 1 hour | Planned rollback |
| Low (P3) | < 4 hours | Fix forward or rollback |

---

## Contact Information

**Escalation Path:**
1. On-call engineer
2. Team lead
3. Engineering manager
4. AWS Support (if infrastructure issue)

**Emergency Contacts:**
- On-call: [PagerDuty/Slack]
- AWS Support: [Support case]
- Stakeholders: [Email list]
