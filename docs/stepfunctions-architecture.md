# IAL Step Functions Architecture

## Overview

The IAL (Infrastructure as Logic) Step Functions implementation provides enterprise-grade orchestration for infrastructure deployment, drift management, and compliance validation.

## Architecture Components

### 1. Phase Pipeline (Standard)
- **Purpose**: End-to-end infrastructure deployment orchestration
- **Type**: Standard (for complex workflows with human approval)
- **Triggers**: GitHub Actions, Manual execution
- **Flow**: Circuit Breaker → Plan → Policy Checks → Apply → Audit → MCP Validations

### 2. Drift Auto-Heal (Express)
- **Purpose**: Automated drift detection and reconciliation
- **Type**: Express (for high-frequency, cost-optimized execution)
- **Triggers**: EventBridge (every 15 minutes)
- **Flow**: Drift Flag Check → Detect → Classify → Auto-Reconcile/PR

### 3. Reverse Sync (Standard)
- **Purpose**: Import unmanaged resources into GitOps
- **Type**: Standard (for complex PR workflows)
- **Triggers**: Manual, Drift detection
- **Flow**: Discover → Generate YAML → Create PR → Auto-merge → Re-audit

## Lambda Wrappers

### Core Operations
- `ial-circuit-guard-lambda`: SSM-based circuit breaker
- `ial-plan-lambda`: CloudFormation plan/changeset generation
- `ial-apply-lambda`: CloudFormation changeset execution
- `ial-audit-validator-lambda`: Creation completeness validation
- `ial-rollback-lambda`: SAGA pattern rollback orchestration

### Drift Management
- `ial-drift-flag-check-lambda`: Drift flag state verification
- `ial-drift-detect-lambda`: Resource drift detection
- `ial-drift-reconcile-lambda`: Safe drift auto-reconciliation
- `ial-reverse-sync-lambda`: Unmanaged resource discovery and YAML generation

### MCP Integrations
- `ial-wa-mcp-lambda`: Well-Architected reviews and scoring
- `ial-finops-mcp-lambda`: Cost analysis and optimization
- `ial-compliance-runner-lambda`: IAL Config Rules validation
- `ial-policy-checks-lambda`: OPA/Conftest validation
- `ial-policy-cfnguard-lambda`: CFN-Guard validation
- `ial-github-mcp-lambda`: GitHub PR automation

### Utilities
- `ial-metrics-publisher-lambda`: CloudWatch metrics publishing

## Security & IAM

### Least Privilege Principles
- Step Functions execution role: Limited to Lambda invocation and logging
- Lambda execution roles: Scoped to specific AWS services (CFN, DynamoDB, SSM, S3)
- EventBridge role: Limited to Step Functions execution
- X-Ray tracing enabled for observability

### Circuit Breaker
- SSM Parameters: `/ial/circuit_breaker/{state,max_inflight,retry_after_sec}`
- States: `closed` (normal), `half_open` (testing), `open` (blocked)
- Fail-safe: Defaults to `closed` if SSM unavailable

## Monitoring & Observability

### CloudWatch Metrics
- `IAL/Creation/Completeness`: Infrastructure creation completeness percentage
- `IAL/Drift/Detected`: Count of drift detections by type (Safe/Risky)
- `IAL/Drift/Reconciled`: Count of successful auto-reconciliations
- `IAL/Circuit/State`: Circuit breaker state (0=closed, 1=half_open, 2=open)
- `IAL/ReverseSync/ResourcesImported`: Count of imported resources

### CloudWatch Alarms
- `IAL-CircuitBreaker-Open`: Circuit breaker open > 5 minutes
- `IAL-CreationCompleteness-Low`: Completeness < 100%
- `IAL-StepFunctions-Failures`: Step Functions execution failures
- `IAL-DriftDetection-High`: High drift volume (>10 in 15min)

### X-Ray Tracing
- End-to-end request tracing across Step Functions and Lambda
- Service map visualization
- Performance bottleneck identification

### CloudWatch Dashboard
- Real-time operational metrics
- Execution success/failure rates
- Lambda performance and errors
- Recent error logs

## Deployment

### Prerequisites
1. AWS CLI configured with appropriate permissions
2. IAM roles deployed (`ial-stepfunctions-roles`, `ial-lambda-roles`)
3. SSM parameters configured for circuit breaker

### Deployment Scripts
```bash
# Phase 1-2: Core infrastructure
./scripts/deploy_stepfunctions.sh

# Phase 3: Drift automation
./scripts/deploy_drift_automation.sh

# Phase 4: MCP integration
./scripts/deploy_mcp_integration.sh

# Phase 5: Observability
./scripts/create_dashboard.sh
```

### Testing
```bash
# Smoke tests
./scripts/test_stepfunctions.sh

# Manual execution
aws stepfunctions start-execution \
  --state-machine-arn "arn:aws:states:REGION:ACCOUNT:stateMachine:ial-phase-pipeline" \
  --input '{"phase":"00-foundation","region":"us-east-1"}'
```

## Integration Points

### GitHub Actions
- Automatic phase detection on push/PR
- Step Functions execution per changed phase
- Artifact collection and reporting
- Deployment status updates

### Decision Ledger
- All MCP actions logged with rationale
- Drift flag changes tracked
- Compliance violations recorded
- Audit trail for all operations

### Drift Flag Integration (Phase 11)
- `ENABLED`: Normal drift detection and auto-reconciliation
- `PAUSED`: Detect drift but generate PR instead of auto-heal
- `DISABLED`: Skip drift detection entirely
- TTL-based auto-resumption

## Cost Optimization

### Express vs Standard
- **Express**: Drift Auto-Heal (high frequency, low cost)
- **Standard**: Phase Pipeline, Reverse Sync (complex workflows)

### Resource Efficiency
- Lambda memory optimized per function type
- EventBridge scheduling (15min intervals)
- CloudWatch log retention (7-14 days)
- X-Ray sampling rules (10% sample rate)

## Troubleshooting

### Common Issues
1. **Circuit Breaker Open**: Check SSM parameters and recent failures
2. **Lambda Timeouts**: Increase memory allocation or timeout values
3. **IAM Permissions**: Verify least-privilege roles have required permissions
4. **Drift Flag Issues**: Check DynamoDB table and TTL configuration

### Debug Tools
- CloudWatch Logs: `/aws/stepfunctions/ial-*`
- X-Ray Service Map: End-to-end request tracing
- Step Functions Console: Execution history and visual workflow
- Lambda Console: Function metrics and error details

## Future Enhancements

### Planned Features
- Multi-region deployment support
- Advanced retry strategies with jitter
- Custom MCP server integrations
- Enhanced GitHub integration (real API)
- Cost forecasting and budgeting

### Scalability Considerations
- Lambda concurrency limits
- Step Functions execution limits
- DynamoDB read/write capacity
- EventBridge rule limits
