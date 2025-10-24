#!/usr/bin/env python3
"""Deployment Health Check - Continuous Monitoring"""

import boto3
import json
import time
from datetime import datetime, timedelta

dynamodb = boto3.client('dynamodb')
sns = boto3.client('sns')

def main():
    """Run deployment health check"""
    
    print("🏥 Running deployment health check...")
    
    # 1. Check for stuck deployments
    stuck_resources = check_stuck_deployments()
    
    # 2. Check for failed resources
    failed_resources = check_failed_resources()
    
    # 3. Check deployment progress
    progress = check_deployment_progress()
    
    # 4. Generate health report
    health_report = {
        'timestamp': datetime.utcnow().isoformat(),
        'stuck_resources': stuck_resources,
        'failed_resources': failed_resources,
        'progress': progress,
        'status': determine_health_status(stuck_resources, failed_resources, progress)
    }
    
    # 5. Save report
    save_health_report(health_report)
    
    # 6. Send alerts if needed
    if health_report['status'] in ['CRITICAL', 'WARNING']:
        send_health_alert(health_report)
    
    print(f"✅ Health check complete: {health_report['status']}")

def check_stuck_deployments():
    """Check for resources stuck in deployment"""
    
    # Resources older than 30 minutes without completion
    cutoff_time = datetime.utcnow() - timedelta(minutes=30)
    
    try:
        response = dynamodb.scan(
            TableName='mcp-provisioning-checklist',
            FilterExpression='#status = :status AND #timestamp < :cutoff',
            ExpressionAttributeNames={
                '#status': 'Status',
                '#timestamp': 'Timestamp'
            },
            ExpressionAttributeValues={
                ':status': {'S': 'InProgress'},
                ':cutoff': {'S': cutoff_time.isoformat()}
            }
        )
        
        stuck = []
        for item in response.get('Items', []):
            stuck.append({
                'resource': item['ResourceName']['S'],
                'phase': item.get('Phase', {}).get('S', 'unknown'),
                'stuck_since': item.get('Timestamp', {}).get('S', 'unknown')
            })
        
        return stuck
        
    except Exception as e:
        print(f"❌ Error checking stuck deployments: {e}")
        return []

def check_failed_resources():
    """Check for failed resource deployments"""
    
    try:
        response = dynamodb.query(
            TableName='mcp-provisioning-checklist',
            KeyConditionExpression='#proj = :p',
            FilterExpression='#status = :status',
            ExpressionAttributeNames={
                '#proj': 'Project',
                '#status': 'Status'
            },
            ExpressionAttributeValues={
                ':p': {'S': 'ial'},
                ':status': {'S': 'Failed'}
            }
        )
        
        failed = []
        for item in response.get('Items', []):
            failed.append({
                'resource': item['ResourceName']['S'],
                'phase': item.get('Phase', {}).get('S', 'unknown'),
                'error': item.get('ErrorMessage', {}).get('S', 'Unknown error'),
                'failed_at': item.get('Timestamp', {}).get('S', 'unknown')
            })
        
        return failed
        
    except Exception as e:
        print(f"❌ Error checking failed resources: {e}")
        return []

def check_deployment_progress():
    """Check overall deployment progress"""
    
    try:
        # Count by status
        response = dynamodb.scan(
            TableName='mcp-provisioning-checklist'
        )
        
        status_counts = {}
        total_resources = 0
        
        for item in response.get('Items', []):
            status = item.get('Status', {}).get('S', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            total_resources += 1
        
        # Calculate progress
        created = status_counts.get('Created', 0)
        progress_rate = (created / total_resources * 100) if total_resources > 0 else 0
        
        return {
            'total_resources': total_resources,
            'created': created,
            'failed': status_counts.get('Failed', 0),
            'in_progress': status_counts.get('InProgress', 0),
            'deleted': status_counts.get('Deleted', 0),
            'progress_rate': progress_rate,
            'status_breakdown': status_counts
        }
        
    except Exception as e:
        print(f"❌ Error checking deployment progress: {e}")
        return {'total_resources': 0, 'progress_rate': 0}

def determine_health_status(stuck, failed, progress):
    """Determine overall deployment health status"""
    
    if failed:
        return 'CRITICAL'
    
    if stuck:
        return 'WARNING'
    
    if progress['progress_rate'] < 50:
        return 'WARNING'
    
    if progress['progress_rate'] >= 95:
        return 'HEALTHY'
    
    return 'MONITORING'

def save_health_report(report):
    """Save health report to file"""
    
    import os
    os.makedirs('/home/ial/reports', exist_ok=True)
    
    with open('/home/ial/reports/deployment_health.json', 'w') as f:
        json.dump(report, f, indent=2)

def send_health_alert(report):
    """Send health alert via SNS"""
    
    try:
        topic_arn = f"arn:aws:sns:{boto3.Session().region_name}:{boto3.client('sts').get_caller_identity()['Account']}:ial-alerts-critical"
        
        message = f"""
🚨 DEPLOYMENT HEALTH ALERT

Status: {report['status']}
Timestamp: {report['timestamp']}

Progress: {report['progress']['created']}/{report['progress']['total_resources']} ({report['progress']['progress_rate']:.1f}%)

Issues:
- Stuck Resources: {len(report['stuck_resources'])}
- Failed Resources: {len(report['failed_resources'])}

Action Required: Review deployment status and resolve issues.
        """
        
        sns.publish(
            TopicArn=topic_arn,
            Subject=f"IaL Deployment Health: {report['status']}",
            Message=message.strip()
        )
        
        print("📧 Health alert sent")
        
    except Exception as e:
        print(f"⚠️ Could not send alert: {e}")

if __name__ == "__main__":
    main()
