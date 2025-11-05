# IAL Service Level Objectives (SLOs)

## Overview

This document defines the Service Level Objectives (SLOs) for the Infrastructure as Language (IAL) platform. These SLOs ensure enterprise-grade reliability, performance, and cost efficiency.

## SLO Definitions

### 1. Creation/Completeness SLO
- **Objective**: 95th percentile of creation completeness must be 100%
- **Measurement**: Percentage of resources successfully created vs desired state
- **Target**: p95 = 100%
- **Measurement Window**: 24 hours
- **Alert Threshold**: < 100%

### 2. Auto-Heal Duration SLO
- **Objective**: 90th percentile of safe drift auto-healing must complete within 10 minutes
- **Measurement**: Time from drift detection to successful reconciliation
- **Target**: p90 ≤ 10 minutes
- **Measurement Window**: 24 hours
- **Alert Threshold**: > 10 minutes

### 3. LLM Cost Per Conversation SLO
- **Objective**: Average LLM cost per conversation must not exceed $0.15
- **Measurement**: Total LLM costs divided by number of conversations
- **Target**: ≤ $0.15 per conversation
- **Measurement Window**: 24 hours
- **Alert Threshold**: > $0.15

### 4. LLM Latency SLO
- **Objective**: 95th percentile of LLM response latency must not exceed 2000ms
- **Measurement**: Time from LLM request to response
- **Target**: p95 ≤ 2000ms
- **Measurement Window**: 24 hours
- **Alert Threshold**: > 2000ms

## Monitoring and Alerting

### CloudWatch Metrics
All SLO metrics are published to CloudWatch under the `IAL/SLO` namespace:
- `SLO_creation_completeness_p95`
- `SLO_autoheal_duration_p90`
- `SLO_llm_cost_per_conversation`
- `SLO_llm_latency_p95`

### Status Metrics
Binary status metrics (1 = PASS, 0 = FAIL):
- `SLO_creation_completeness_p95_status`
- `SLO_autoheal_duration_p90_status`
- `SLO_llm_cost_per_conversation_status`
- `SLO_llm_latency_p95_status`

### Alarms
CloudWatch alarms are configured for each SLO:
- **Creation Completeness Alarm**: Triggers when status < 1 for 2 consecutive periods
- **Auto-Heal Duration Alarm**: Triggers when status < 1 for 2 consecutive periods
- **LLM Cost Alarm**: Triggers when status < 1 for 2 consecutive periods
- **LLM Latency Alarm**: Triggers when status < 1 for 2 consecutive periods

### SNS Notifications
SLO violations trigger SNS notifications to the `ial-slo-violations` topic.

## Dashboard

The Enterprise Observability Dashboard provides real-time visibility into all SLOs:
- **URL**: Available in CloudFormation outputs
- **Refresh**: Every 5 minutes
- **Widgets**: SLO metrics, trends, and status indicators

## SLO Monitoring Process

### Automated Monitoring
- **Frequency**: Every 5 minutes via EventBridge scheduled rule
- **Lambda Function**: `ial-slo-monitoring` calculates and publishes metrics
- **Data Source**: CloudWatch metrics from IAL components

### Manual Review
- **Frequency**: Weekly SLO review meetings
- **Participants**: Platform team, stakeholders
- **Artifacts**: SLO dashboard, violation reports, trend analysis

## SLO Violation Response

### Immediate Actions (< 1 hour)
1. **Acknowledge**: Confirm SLO violation via dashboard/alerts
2. **Assess**: Determine impact and root cause
3. **Communicate**: Notify stakeholders if user-impacting

### Short-term Actions (< 24 hours)
1. **Mitigate**: Implement temporary fixes to restore SLO compliance
2. **Monitor**: Verify SLO recovery and stability
3. **Document**: Record incident details and actions taken

### Long-term Actions (< 1 week)
1. **Root Cause Analysis**: Deep dive into violation causes
2. **Preventive Measures**: Implement changes to prevent recurrence
3. **SLO Review**: Assess if SLO targets need adjustment

## Error Budget

### Calculation
- **Creation Completeness**: 0% error budget (must be 100%)
- **Auto-Heal Duration**: 10% error budget (p90 can exceed 10 min for 10% of cases)
- **LLM Cost**: 5% error budget (can exceed $0.15 for 5% of conversations)
- **LLM Latency**: 5% error budget (p95 can exceed 2000ms for 5% of time)

### Error Budget Policy
- **Green (0-50% consumed)**: Normal operations
- **Yellow (50-90% consumed)**: Increased monitoring, consider preventive actions
- **Red (90-100% consumed)**: Halt non-critical changes, focus on reliability

## SLO Evolution

### Review Cycle
- **Monthly**: Review SLO performance and trends
- **Quarterly**: Assess SLO targets and adjust if needed
- **Annually**: Comprehensive SLO framework review

### Target Adjustment Criteria
- **Tighten**: If consistently exceeding targets by >20%
- **Relax**: If missing targets >50% of the time despite best efforts
- **New SLOs**: Add based on user feedback and business requirements

## Integration with IAL Components

### Feature Flags
- SLO monitoring can be paused using feature flags
- State: `PAUSED` allows maintenance without SLO violations

### Circuit Breaker
- SLO violations can trigger circuit breaker to protect system
- Automatic recovery when SLOs return to compliance

### Audit Enforcement
- Creation completeness SLO enforced at pipeline level
- Deployments fail if completeness < 100%

## Troubleshooting

### Common Issues
1. **Missing Metrics**: Check Lambda function logs and permissions
2. **False Alarms**: Verify metric calculation logic and thresholds
3. **Dashboard Issues**: Confirm CloudWatch dashboard permissions

### Debug Commands
```bash
# Check SLO monitoring Lambda logs
aws logs tail /aws/lambda/ial-slo-monitoring --follow

# Get current SLO metrics
aws cloudwatch get-metric-statistics \
  --namespace IAL/SLO \
  --metric-name SLO_creation_completeness_p95 \
  --start-time 2025-11-03T00:00:00Z \
  --end-time 2025-11-03T23:59:59Z \
  --period 3600 \
  --statistics Average

# Check alarm status
aws cloudwatch describe-alarms \
  --alarm-names ial-slo-creation-completeness
```

## References
- [CloudWatch Metrics Documentation](https://docs.aws.amazon.com/cloudwatch/latest/monitoring/working_with_metrics.html)
- [SLO Best Practices](https://sre.google/sre-book/service-level-objectives/)
- [IAL Architecture Documentation](../ARCHITECTURE.md)
