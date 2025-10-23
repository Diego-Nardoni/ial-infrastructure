# Security Validation Checklist

Comprehensive security checklist for the Spring Redis Application infrastructure.

## Identity and Access Management (IAM)

### IAM Roles and Policies

- [ ] ECS Task Execution Role has minimum required permissions
- [ ] ECS Task Role follows principle of least privilege
- [ ] GitHub Actions Role has only deployment permissions
- [ ] No IAM users with access keys (use roles instead)
- [ ] IAM policies use specific resource ARNs (not *)
- [ ] No inline policies with wildcard permissions
- [ ] MFA enabled for all human users
- [ ] IAM Access Analyzer enabled and reviewed

**Validation Commands:**

```bash
# Check IAM roles
aws iam get-role --role-name ${PROJECT_NAME}-ecs-task-execution-role --region ${AWS_REGION}
aws iam get-role --role-name ${PROJECT_NAME}-ecs-task-role --region ${AWS_REGION}
aws iam get-role --role-name ${PROJECT_NAME}-github-actions-role --region ${AWS_REGION}

# List attached policies
aws iam list-attached-role-policies --role-name ${PROJECT_NAME}-ecs-task-role --region ${AWS_REGION}

# Check for wildcard permissions
aws iam get-role-policy --role-name ${PROJECT_NAME}-ecs-task-role --policy-name <policy-name> --region ${AWS_REGION}
```

---

## Network Security

### VPC Configuration

- [ ] VPC has private subnets for ECS tasks
- [ ] VPC has database subnets for Redis
- [ ] Public subnets only for ALB and NAT Gateways
- [ ] Network ACLs configured (if used)
- [ ] VPC Flow Logs enabled
- [ ] DNS resolution enabled
- [ ] DNS hostnames enabled

**Validation Commands:**

```bash
# Check VPC configuration
aws ec2 describe-vpcs --vpc-ids ${VPC_ID} --region ${AWS_REGION}

# Check subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=${VPC_ID}" --region ${AWS_REGION}

# Verify Flow Logs
aws ec2 describe-flow-logs --filter "Name=resource-id,Values=${VPC_ID}" --region ${AWS_REGION}
```

---

### Security Groups

- [ ] ECS security group allows inbound only from ALB
- [ ] ALB security group allows inbound only from CloudFront (if used)
- [ ] Redis security group allows inbound only from ECS
- [ ] No security groups with 0.0.0.0/0 inbound (except ALB on 443)
- [ ] All security groups have descriptive names and descriptions
- [ ] Unused security groups removed

**Validation Commands:**

```bash
# Check ECS security group
aws ec2 describe-security-groups --group-ids ${ECS_SG} --region ${AWS_REGION}

# Check for overly permissive rules
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.cidr,Values=0.0.0.0/0" \
  --query 'SecurityGroups[?IpPermissions[?FromPort!=`443`]]' \
  --region ${AWS_REGION}
```

---

## Data Protection

### Encryption at Rest

- [ ] ECS task storage encrypted with KMS
- [ ] Redis encrypted at rest with KMS
- [ ] CloudWatch Logs encrypted with KMS
- [ ] ECR repository encrypted with KMS
- [ ] Parameter Store values encrypted with KMS
- [ ] S3 buckets encrypted (if used)
- [ ] KMS key rotation enabled

**Validation Commands:**

```bash
# Check KMS keys
aws kms describe-key --key-id ${KMS_ECS_KEY_ID} --region ${AWS_REGION}
aws kms get-key-rotation-status --key-id ${KMS_ECS_KEY_ID} --region ${AWS_REGION}

# Check ECR encryption
aws ecr describe-repositories --repository-names ${PROJECT_NAME} --region ${AWS_REGION}

# Check Redis encryption
aws elasticache describe-serverless-caches --serverless-cache-name ${PROJECT_NAME}-redis --region ${AWS_REGION}
```

---

### Encryption in Transit

- [ ] ALB uses HTTPS with valid SSL certificate
- [ ] CloudFront uses HTTPS with valid SSL certificate
- [ ] ECS to Redis connection encrypted (TLS)
- [ ] ECS to Parameter Store uses HTTPS
- [ ] Minimum TLS version 1.2 enforced
- [ ] Strong cipher suites configured

**Validation Commands:**

```bash
# Check ALB listener
aws elbv2 describe-listeners --load-balancer-arn ${ALB_ARN} --region ${AWS_REGION}

# Check SSL policy
aws elbv2 describe-ssl-policies --names ELBSecurityPolicy-TLS-1-2-2017-01 --region ${AWS_REGION}

# Test TLS connection
openssl s_client -connect ${ALB_DNS_NAME}:443 -tls1_2
```

---

## Application Security

### Container Security

- [ ] Docker image scanned for vulnerabilities (ECR scan)
- [ ] Base image is minimal (Alpine/Distroless)
- [ ] No secrets in Docker image
- [ ] Container runs as non-root user
- [ ] Read-only root filesystem (if possible)
- [ ] Resource limits configured (CPU, memory)
- [ ] Health checks configured

**Validation Commands:**

```bash
# Check ECR scan results
aws ecr describe-image-scan-findings \
  --repository-name ${PROJECT_NAME} \
  --image-id imageTag=latest \
  --region ${AWS_REGION}

# Check task definition security
aws ecs describe-task-definition \
  --task-definition ${PROJECT_NAME}-task \
  --query 'taskDefinition.containerDefinitions[0].[user,readonlyRootFilesystem,privileged]' \
  --region ${AWS_REGION}
```

---

### Secrets Management

- [ ] No hardcoded secrets in code
- [ ] No secrets in environment variables
- [ ] All secrets in Parameter Store (SecureString)
- [ ] Secrets encrypted with KMS
- [ ] Secrets rotation enabled (if applicable)
- [ ] Access to secrets logged and monitored

**Validation Commands:**

```bash
# List parameters
aws ssm describe-parameters --region ${AWS_REGION}

# Check parameter encryption
aws ssm get-parameter --name "/${PROJECT_NAME}/redis/host" --with-decryption --region ${AWS_REGION}

# Check parameter access logs
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=/${PROJECT_NAME}/redis/host \
  --region ${AWS_REGION}
```

---

## Monitoring and Logging

### CloudWatch Logs

- [ ] ECS task logs sent to CloudWatch
- [ ] VPC Flow Logs enabled
- [ ] ALB access logs enabled
- [ ] CloudFront logs enabled (if used)
- [ ] WAF logs enabled (if used)
- [ ] Log retention configured
- [ ] Logs encrypted with KMS

**Validation Commands:**

```bash
# Check log groups
aws logs describe-log-groups --log-group-name-prefix /ecs/${PROJECT_NAME} --region ${AWS_REGION}

# Check log retention
aws logs describe-log-groups \
  --log-group-name-prefix /ecs/${PROJECT_NAME} \
  --query 'logGroups[*].[logGroupName,retentionInDays]' \
  --region ${AWS_REGION}

# Check VPC Flow Logs
aws ec2 describe-flow-logs --filter "Name=resource-id,Values=${VPC_ID}" --region ${AWS_REGION}
```

---

### Security Monitoring

- [ ] GuardDuty enabled
- [ ] Security Hub enabled
- [ ] AWS Config enabled
- [ ] CloudTrail enabled
- [ ] CloudWatch alarms for security events
- [ ] SNS notifications configured
- [ ] Regular review of security findings

**Validation Commands:**

```bash
# Check GuardDuty
aws guardduty list-detectors --region ${AWS_REGION}

# Check Security Hub
aws securityhub describe-hub --region ${AWS_REGION}

# Check Config
aws configservice describe-configuration-recorders --region ${AWS_REGION}

# Check CloudTrail
aws cloudtrail describe-trails --region ${AWS_REGION}
```

---

## Web Application Firewall (WAF)

### WAF Configuration

- [ ] WAF WebACL attached to CloudFront/ALB
- [ ] Rate limiting rules configured
- [ ] AWS Managed Rules enabled
- [ ] Geo-blocking configured (if needed)
- [ ] IP reputation lists enabled
- [ ] SQL injection protection enabled
- [ ] XSS protection enabled
- [ ] WAF logs enabled

**Validation Commands:**

```bash
# Check WAF WebACL
aws wafv2 get-web-acl --name ${PROJECT_NAME}-waf --scope CLOUDFRONT --region us-east-1

# List WAF rules
aws wafv2 list-web-acls --scope CLOUDFRONT --region us-east-1

# Check WAF logging
aws wafv2 get-logging-configuration --resource-arn ${WEB_ACL_ARN} --region us-east-1
```

---

## Compliance and Governance

### Resource Tagging

- [ ] All resources tagged with Project
- [ ] All resources tagged with Environment
- [ ] All resources tagged with ManagedBy
- [ ] All resources tagged with Executor
- [ ] Cost allocation tags enabled
- [ ] Tag policies enforced (if using AWS Organizations)

**Validation Commands:**

```bash
# Check resource tags
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=${PROJECT_NAME} \
  --region ${AWS_REGION}

# Find untagged resources
aws resourcegroupstaggingapi get-resources \
  --resource-type-filters ec2 ecs elasticache \
  --region ${AWS_REGION} \
  | jq '.ResourceTagMappingList[] | select(.Tags | length == 0)'
```

---

### Backup and Recovery

- [ ] Redis automated backups enabled
- [ ] Backup retention configured
- [ ] Disaster recovery plan documented
- [ ] Backup restoration tested
- [ ] Multi-region deployment (if required)
- [ ] RTO and RPO defined

**Validation Commands:**

```bash
# Check Redis backup configuration
aws elasticache describe-serverless-caches \
  --serverless-cache-name ${PROJECT_NAME}-redis \
  --query 'ServerlessCaches[0].[SnapshotRetentionLimit,DailySnapshotTime]' \
  --region ${AWS_REGION}

# List available snapshots
aws elasticache describe-serverless-cache-snapshots \
  --serverless-cache-name ${PROJECT_NAME}-redis \
  --region ${AWS_REGION}
```

---

## Incident Response

### Incident Response Plan

- [ ] Incident response plan documented
- [ ] Security contact information updated
- [ ] Escalation procedures defined
- [ ] Forensics procedures documented
- [ ] Communication plan established
- [ ] Post-incident review process defined

---

## Security Testing

### Penetration Testing

- [ ] Penetration testing performed (if required)
- [ ] Vulnerability scanning scheduled
- [ ] Security findings remediated
- [ ] Retest after remediation

---

### Automated Security Scanning

- [ ] Bedrock validation in CI/CD pipeline
- [ ] ECR image scanning enabled
- [ ] Dependency scanning enabled
- [ ] SAST tools integrated (if applicable)
- [ ] Security findings reviewed regularly

**Validation Commands:**

```bash
# Check ECR scan on push
aws ecr describe-repositories \
  --repository-names ${PROJECT_NAME} \
  --query 'repositories[0].imageScanningConfiguration' \
  --region ${AWS_REGION}

# Get latest scan results
aws ecr describe-image-scan-findings \
  --repository-name ${PROJECT_NAME} \
  --image-id imageTag=latest \
  --region ${AWS_REGION}
```

---

## Security Score

### Scoring Criteria

| Category | Weight | Score | Status |
|----------|--------|-------|--------|
| IAM | 20% | /100 | ⬜ |
| Network Security | 20% | /100 | ⬜ |
| Data Protection | 20% | /100 | ⬜ |
| Application Security | 15% | /100 | ⬜ |
| Monitoring & Logging | 10% | /100 | ⬜ |
| WAF | 5% | /100 | ⬜ |
| Compliance | 5% | /100 | ⬜ |
| Incident Response | 5% | /100 | ⬜ |
| **Total** | **100%** | **/100** | ⬜ |

**Target Score:** ≥ 90/100

---

## Remediation Priority

### Critical (Fix Immediately)

- Publicly accessible databases
- Unencrypted sensitive data
- Overly permissive IAM policies
- Missing security groups
- Disabled security services

### High (Fix within 24 hours)

- Missing encryption at rest
- Weak TLS configuration
- Missing CloudWatch alarms
- Unpatched vulnerabilities (CVSS ≥ 7.0)

### Medium (Fix within 1 week)

- Missing resource tags
- Suboptimal security group rules
- Missing backup configuration
- Unpatched vulnerabilities (CVSS 4.0-6.9)

### Low (Fix within 1 month)

- Documentation gaps
- Optimization opportunities
- Nice-to-have security enhancements

---

## Security Review Schedule

- **Daily:** Review GuardDuty findings
- **Weekly:** Review Security Hub compliance
- **Monthly:** Full security checklist review
- **Quarterly:** Penetration testing
- **Annually:** Security audit

---

## Compliance Frameworks

### AWS Well-Architected Framework - Security Pillar

- [ ] SEC01: Operate workload securely
- [ ] SEC02: Manage identities for people and machines
- [ ] SEC03: Manage permissions for people and machines
- [ ] SEC04: Detect and investigate security events
- [ ] SEC05: Protect network resources
- [ ] SEC06: Protect compute resources
- [ ] SEC07: Classify data
- [ ] SEC08: Protect data at rest
- [ ] SEC09: Protect data in transit
- [ ] SEC10: Anticipate, respond to, and recover from incidents

---

## Additional Resources

- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [AWS Well-Architected Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)
- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
