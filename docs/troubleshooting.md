# Troubleshooting Guide

Common issues and solutions for the Spring Redis Application deployment.

## Table of Contents

1. [Deployment Issues](#deployment-issues)
2. [Application Issues](#application-issues)
3. [Network Issues](#network-issues)
4. [Security Issues](#security-issues)
5. [Performance Issues](#performance-issues)
6. [Cost Issues](#cost-issues)

---

## Deployment Issues

### Issue: DynamoDB Table Already Exists

**Symptom:**
```
ResourceInUseException: Table already exists
```

**Solution:**
```bash
# Check if table exists
aws dynamodb describe-table --table-name ${PROJECT_NAME}-ial-state --region ${AWS_REGION}

# If exists, either use it or delete and recreate
aws dynamodb delete-table --table-name ${PROJECT_NAME}-ial-state --region ${AWS_REGION}
```

---

### Issue: KMS Key Creation Fails

**Symptom:**
```
AccessDeniedException: User is not authorized to perform: kms:CreateKey
```

**Solution:**
```bash
# Verify IAM permissions
aws iam get-user --query 'User.Arn' --output text

# Check attached policies
aws iam list-attached-user-policies --user-name <your-username>

# Required permission: kms:CreateKey, kms:CreateAlias, kms:EnableKeyRotation
```

---

### Issue: VPC Creation Fails - CIDR Conflict

**Symptom:**
```
CidrConflict: The CIDR '10.0.0.0/16' conflicts with another subnet
```

**Solution:**
```bash
# List existing VPCs
aws ec2 describe-vpcs --region ${AWS_REGION}

# Use different CIDR block
# Edit phases/03-networking.yaml and change CIDR to 10.1.0.0/16 or 172.16.0.0/16
```

---

### Issue: NAT Gateway Creation Fails

**Symptom:**
```
InvalidSubnet: The subnet must be in an available state
```

**Solution:**
```bash
# Verify subnet state
aws ec2 describe-subnets --subnet-ids ${PUBLIC_SUBNET_1} --region ${AWS_REGION}

# Ensure Internet Gateway is attached first
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=${VPC_ID}" --region ${AWS_REGION}
```

---

### Issue: ECS Task Fails to Start

**Symptom:**
```
CannotPullContainerError: Error response from daemon
```

**Solution:**
```bash
# Verify ECR repository exists
aws ecr describe-repositories --repository-names ${PROJECT_NAME} --region ${AWS_REGION}

# Check if image exists
aws ecr list-images --repository-name ${PROJECT_NAME} --region ${AWS_REGION}

# Verify ECS task execution role has ECR permissions
aws iam get-role-policy --role-name ${PROJECT_NAME}-ecs-task-execution-role --policy-name ECRAccess
```

---

### Issue: ECS Task Fails - Parameter Store Access Denied

**Symptom:**
```
ResourceInitializationError: unable to pull secrets or registry auth
```

**Solution:**
```bash
# Verify task execution role has SSM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::${AWS_ACCOUNT_ID}:role/${PROJECT_NAME}-ecs-task-execution-role \
  --action-names ssm:GetParameters \
  --resource-arns arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT_ID}:parameter/${PROJECT_NAME}/*

# Check if parameters exist
aws ssm get-parameters --names "/${PROJECT_NAME}/redis/host" --region ${AWS_REGION}
```

---

### Issue: Redis Connection Timeout

**Symptom:**
```
RedisConnectionException: Unable to connect to Redis
```

**Solution:**
```bash
# Verify Redis is available
aws elasticache describe-serverless-caches \
  --serverless-cache-name ${PROJECT_NAME}-redis \
  --query 'ServerlessCaches[0].Status' \
  --region ${AWS_REGION}

# Check security group rules
aws ec2 describe-security-groups --group-ids ${REDIS_SG} --region ${AWS_REGION}

# Verify ECS security group can reach Redis (port 6379)
# Ensure Redis security group allows inbound from ECS security group
```

---

### Issue: ALB Health Check Failing

**Symptom:**
```
Target health check failed: Connection refused
```

**Solution:**
```bash
# Check ECS task logs
aws logs tail /ecs/${PROJECT_NAME} --follow --region ${AWS_REGION}

# Verify application is listening on correct port (8080)
# Check security group allows ALB to reach ECS tasks

# Test health endpoint
aws ecs execute-command \
  --cluster ${PROJECT_NAME}-cluster \
  --task <task-id> \
  --container ${PROJECT_NAME} \
  --command "curl localhost:8080/actuator/health" \
  --interactive
```

---

## Application Issues

### Issue: Application Crashes on Startup

**Symptom:**
```
ECS task stopped with exit code 1
```

**Solution:**
```bash
# Check CloudWatch Logs
aws logs tail /ecs/${PROJECT_NAME} --follow --region ${AWS_REGION}

# Common causes:
# 1. Missing environment variables
# 2. Redis connection failure
# 3. Invalid configuration

# Verify all parameters are set
aws ssm get-parameters-by-path --path "/${PROJECT_NAME}/" --region ${AWS_REGION}
```

---

### Issue: Redis Data Not Persisting

**Symptom:**
Data disappears after application restart

**Solution:**
```bash
# Verify Redis Serverless configuration
aws elasticache describe-serverless-caches \
  --serverless-cache-name ${PROJECT_NAME}-redis \
  --region ${AWS_REGION}

# Check snapshot configuration
# Redis Serverless automatically handles persistence
# Verify application is using correct Redis endpoint
```

---

### Issue: High Memory Usage

**Symptom:**
ECS tasks restarting due to OOM

**Solution:**
```bash
# Check current memory allocation
aws ecs describe-task-definition \
  --task-definition ${PROJECT_NAME}-task \
  --query 'taskDefinition.memory' \
  --region ${AWS_REGION}

# Increase memory in task definition
# Edit phases/08-ecs-task-service.yaml
# Change memory from 2048 to 4096

# Monitor memory usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=${PROJECT_NAME}-service Name=ClusterName,Value=${PROJECT_NAME}-cluster \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average \
  --region ${AWS_REGION}
```

---

## Network Issues

### Issue: Cannot Access Application via CloudFront

**Symptom:**
CloudFront returns 502 Bad Gateway

**Solution:**
```bash
# Check CloudFront distribution status
aws cloudfront get-distribution --id ${CLOUDFRONT_ID} --query 'Distribution.Status'

# Verify origin (ALB) is healthy
aws elbv2 describe-target-health \
  --target-group-arn ${TARGET_GROUP_ARN} \
  --region ${AWS_REGION}

# Check ALB listener rules
aws elbv2 describe-listeners --load-balancer-arn ${ALB_ARN} --region ${AWS_REGION}

# Test ALB directly
curl -I http://${ALB_DNS_NAME}/actuator/health
```

---

### Issue: VPC Flow Logs Not Appearing

**Symptom:**
No logs in CloudWatch Logs

**Solution:**
```bash
# Verify flow logs are active
aws ec2 describe-flow-logs --filter "Name=resource-id,Values=${VPC_ID}" --region ${AWS_REGION}

# Check IAM role for flow logs
aws iam get-role --role-name ${PROJECT_NAME}-vpc-flow-logs-role

# Verify CloudWatch log group exists
aws logs describe-log-groups --log-group-name-prefix /aws/vpc/${PROJECT_NAME} --region ${AWS_REGION}

# Wait 10-15 minutes for logs to appear (flow logs have delay)
```

---

### Issue: NAT Gateway High Costs

**Symptom:**
Unexpected NAT Gateway charges

**Solution:**
```bash
# Check NAT Gateway data transfer
aws cloudwatch get-metric-statistics \
  --namespace AWS/NATGateway \
  --metric-name BytesOutToDestination \
  --dimensions Name=NatGatewayId,Value=${NAT_GW_ID} \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum \
  --region ${AWS_REGION}

# Consider VPC endpoints for AWS services
# See cost-optimization.md for details
```

---

## Security Issues

### Issue: GuardDuty Findings

**Symptom:**
GuardDuty alerts for suspicious activity

**Solution:**
```bash
# List active findings
aws guardduty list-findings \
  --detector-id ${DETECTOR_ID} \
  --finding-criteria '{"Criterion":{"service.archived":{"Eq":["false"]}}}' \
  --region ${AWS_REGION}

# Get finding details
aws guardduty get-findings \
  --detector-id ${DETECTOR_ID} \
  --finding-ids <finding-id> \
  --region ${AWS_REGION}

# Common findings:
# - UnauthorizedAccess:EC2/SSHBruteForce - Block source IP in NACL
# - Recon:EC2/PortProbeUnprotectedPort - Review security groups
# - CryptoCurrency:EC2/BitcoinTool.B!DNS - Investigate compromised instance
```

---

### Issue: Security Hub Compliance Failures

**Symptom:**
Failed security controls

**Solution:**
```bash
# List failed controls
aws securityhub get-findings \
  --filters '{"ComplianceStatus":[{"Value":"FAILED","Comparison":"EQUALS"}]}' \
  --region ${AWS_REGION}

# Common failures:
# - S3.1: S3 Block Public Access - Enable block public access
# - EC2.2: VPC default security group - Remove rules from default SG
# - IAM.4: Root account access keys - Delete root access keys
```

---

### Issue: WAF Blocking Legitimate Traffic

**Symptom:**
Users receiving 403 Forbidden

**Solution:**
```bash
# Check WAF logs
aws wafv2 get-sampled-requests \
  --web-acl-arn ${WEB_ACL_ARN} \
  --rule-metric-name ALL \
  --scope CLOUDFRONT \
  --time-window StartTime=$(date -u -d '1 hour ago' +%s),EndTime=$(date -u +%s) \
  --max-items 100

# Review blocked requests
# Add IP to allowlist if needed
# Adjust rate limiting rules
```

---

## Performance Issues

### Issue: High Latency

**Symptom:**
Response times > 1 second

**Solution:**
```bash
# Check ALB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=${ALB_NAME} \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --region ${AWS_REGION}

# Check Redis latency
# Enable Redis slow log
# Review application logs for slow queries
# Consider Redis connection pooling optimization
```

---

### Issue: Auto Scaling Not Triggering

**Symptom:**
Tasks not scaling despite high CPU

**Solution:**
```bash
# Check scaling policies
aws application-autoscaling describe-scaling-policies \
  --service-namespace ecs \
  --resource-id service/${PROJECT_NAME}-cluster/${PROJECT_NAME}-service \
  --region ${AWS_REGION}

# Verify CloudWatch alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix ${PROJECT_NAME} \
  --region ${AWS_REGION}

# Check alarm state
aws cloudwatch describe-alarm-history \
  --alarm-name ${PROJECT_NAME}-cpu-high \
  --max-records 10 \
  --region ${AWS_REGION}
```

---

## Cost Issues

### Issue: Unexpected High Costs

**Symptom:**
AWS bill higher than expected

**Solution:**
```bash
# Check Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '1 month ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=SERVICE

# Common cost drivers:
# 1. NAT Gateway data transfer - Use VPC endpoints
# 2. CloudFront data transfer - Review cache settings
# 3. ECS Fargate - Right-size tasks
# 4. Redis Serverless - Monitor ECPU usage

# See cost-optimization.md for detailed strategies
```

---

## Diagnostic Commands

### Check Overall System Health

```bash
# ECS Service
aws ecs describe-services \
  --cluster ${PROJECT_NAME}-cluster \
  --services ${PROJECT_NAME}-service \
  --region ${AWS_REGION}

# Target Health
aws elbv2 describe-target-health \
  --target-group-arn ${TARGET_GROUP_ARN} \
  --region ${AWS_REGION}

# Redis Status
aws elasticache describe-serverless-caches \
  --serverless-cache-name ${PROJECT_NAME}-redis \
  --region ${AWS_REGION}

# CloudWatch Alarms
aws cloudwatch describe-alarms \
  --state-value ALARM \
  --region ${AWS_REGION}
```

---

## Getting Help

If issues persist:

1. Check CloudWatch Logs: `/ecs/${PROJECT_NAME}`
2. Review X-Ray traces for distributed tracing
3. Check Security Hub for security findings
4. Review Cost Explorer for cost anomalies
5. Contact AWS Support with:
   - Account ID
   - Region
   - Resource IDs
   - Error messages
   - CloudWatch log excerpts

---

## Additional Resources

- [AWS ECS Troubleshooting](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/troubleshooting.html)
- [ElastiCache Troubleshooting](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/Troubleshooting.html)
- [ALB Troubleshooting](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html)
- [CloudFront Troubleshooting](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/troubleshooting-distributions.html)
