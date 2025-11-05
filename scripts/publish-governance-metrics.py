#!/usr/bin/env python3
import argparse
import boto3
import json
import os
from datetime import datetime

class GovernanceMetricsPublisher:
    def __init__(self, region='us-east-1'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.namespace = 'IaL/Pipeline'
    
    def publish_governance_metrics(self, compliance_status, budget_status, security_status=None):
        """Publish governance pipeline metrics to CloudWatch"""
        
        metrics = []
        timestamp = datetime.utcnow()
        
        # Compliance metrics
        compliance_value = 1 if compliance_status == 'PASS' else 0
        metrics.append({
            'MetricName': 'ComplianceGate',
            'Value': compliance_value,
            'Unit': 'None',
            'Timestamp': timestamp,
            'Dimensions': [
                {'Name': 'Status', 'Value': compliance_status}
            ]
        })
        
        # Budget metrics
        budget_value = 1 if budget_status == 'PASS' else 0
        metrics.append({
            'MetricName': 'BudgetGate',
            'Value': budget_value,
            'Unit': 'None',
            'Timestamp': timestamp,
            'Dimensions': [
                {'Name': 'Status', 'Value': budget_status}
            ]
        })
        
        # Security metrics
        if security_status:
            security_value = 1 if security_status == 'PASS' else 0
            metrics.append({
                'MetricName': 'SecurityGate',
                'Value': security_value,
                'Unit': 'None',
                'Timestamp': timestamp,
                'Dimensions': [
                    {'Name': 'Status', 'Value': security_status}
                ]
            })
        
        # Overall pipeline execution
        overall_success = all(status == 'PASS' for status in [compliance_status, budget_status, security_status] if status)
        metrics.append({
            'MetricName': 'PipelineExecution',
            'Value': 1 if overall_success else 0,
            'Unit': 'None',
            'Timestamp': timestamp,
            'Dimensions': [
                {'Name': 'Result', 'Value': 'SUCCESS' if overall_success else 'FAILURE'}
            ]
        })
        
        # Deployment blocked metric
        if not overall_success:
            metrics.append({
                'MetricName': 'DeploymentBlocked',
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': timestamp
            })
        
        # Load additional metrics from reports
        self._add_detailed_metrics(metrics, timestamp)
        
        # Publish metrics in batches (CloudWatch limit is 20 per call)
        batch_size = 20
        for i in range(0, len(metrics), batch_size):
            batch = metrics[i:i + batch_size]
            
            try:
                response = self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=batch
                )
                print(f"✅ Published {len(batch)} metrics to CloudWatch")
                
            except Exception as e:
                print(f"❌ Failed to publish metrics batch: {e}")
        
        return len(metrics)
    
    def _add_detailed_metrics(self, metrics, timestamp):
        """Add detailed metrics from report files"""
        
        # Compliance details
        compliance_report = self._load_report('reports/compliance/predeploy_report.json')
        if compliance_report:
            metrics.append({
                'MetricName': 'ComplianceViolations',
                'Value': compliance_report.get('violations_count', 0),
                'Unit': 'Count',
                'Timestamp': timestamp
            })
            
            metrics.append({
                'MetricName': 'ComplianceRulesProcessed',
                'Value': compliance_report.get('rules_processed', 0),
                'Unit': 'Count',
                'Timestamp': timestamp
            })
        
        # Budget details
        budget_report = self._load_report('reports/finops/budget_check.json')
        if budget_report:
            metrics.append({
                'MetricName': 'EstimatedCost',
                'Value': budget_report.get('estimated_cost', 0),
                'Unit': 'None',  # USD
                'Timestamp': timestamp
            })
            
            metrics.append({
                'MetricName': 'BudgetUtilization',
                'Value': budget_report.get('utilization_percent', 0),
                'Unit': 'Percent',
                'Timestamp': timestamp
            })
            
            if budget_report.get('overage', 0) > 0:
                metrics.append({
                    'MetricName': 'BudgetOverage',
                    'Value': budget_report['overage'],
                    'Unit': 'None',  # USD
                    'Timestamp': timestamp
                })
    
    def _load_report(self, report_path):
        """Load report file if it exists"""
        try:
            if os.path.exists(report_path):
                with open(report_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load report {report_path}: {e}")
        
        return None

def main():
    parser = argparse.ArgumentParser(description='Publish governance metrics to CloudWatch')
    parser.add_argument('--compliance-status', required=True, help='Compliance check status')
    parser.add_argument('--budget-status', required=True, help='Budget check status')
    parser.add_argument('--security-status', help='Security check status')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    args = parser.parse_args()
    
    publisher = GovernanceMetricsPublisher(region=args.region)
    
    metrics_count = publisher.publish_governance_metrics(
        compliance_status=args.compliance_status,
        budget_status=args.budget_status,
        security_status=args.security_status
    )
    
    print(f"📊 Published {metrics_count} governance metrics to CloudWatch")

if __name__ == "__main__":
    main()
