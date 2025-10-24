#!/usr/bin/env python3
"""Enhanced Validation Reports with Console Links and Detailed Cost Analysis"""

import boto3
import json
import os
from datetime import datetime
from urllib.parse import quote

def generate_enhanced_report():
    """Generate enhanced validation report with console links and cost details"""
    
    print("📊 Generating Enhanced Validation Report...")
    
    # Get AWS account info
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Get validation data
    validation_data = get_validation_data()
    
    # Generate enhanced report
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'account_id': account_id,
        'region': region,
        'summary': validation_data['summary'],
        'resources': enhance_resources_with_links(validation_data['resources'], account_id, region),
        'cost_analysis': get_detailed_cost_analysis(),
        'console_links': generate_console_links(account_id, region),
        'recommendations': generate_recommendations(validation_data)
    }
    
    # Save enhanced report
    os.makedirs('reports', exist_ok=True)
    with open('reports/enhanced_validation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Generate HTML report
    generate_html_report(report)
    
    # Display summary
    display_enhanced_summary(report)
    
    return report

def get_validation_data():
    """Get current validation data"""
    
    try:
        dynamodb = boto3.client('dynamodb')
        
        response = dynamodb.query(
            TableName='mcp-provisioning-checklist',
            KeyConditionExpression='#proj = :p',
            ExpressionAttributeNames={'#proj': 'Project'},
            ExpressionAttributeValues={':p': {'S': 'ial'}}
        )
        
        resources = []
        for item in response.get('Items', []):
            resources.append({
                'name': item['ResourceName']['S'],
                'type': item['ResourceType']['S'],
                'status': item['Status']['S'],
                'phase': item.get('Phase', {}).get('S', 'unknown'),
                'service': item.get('Service', {}).get('S', 'unknown'),
                'properties': json.loads(item.get('Properties', {}).get('S', '{}'))
            })
        
        summary = {
            'total_resources': len(resources),
            'created_resources': len([r for r in resources if r['status'] == 'Created']),
            'verified_resources': len([r for r in resources if r['status'] == 'Verified']),
            'failed_resources': len([r for r in resources if r['status'] == 'Failed'])
        }
        
        return {'summary': summary, 'resources': resources}
        
    except Exception as e:
        print(f"❌ Error getting validation data: {e}")
        return {'summary': {}, 'resources': []}

def enhance_resources_with_links(resources, account_id, region):
    """Enhance resources with AWS Console links and ARNs"""
    
    enhanced = []
    
    for resource in resources:
        enhanced_resource = resource.copy()
        
        # Generate ARN
        arn = generate_resource_arn(resource, account_id, region)
        enhanced_resource['arn'] = arn
        
        # Generate console link
        console_link = generate_console_link(resource, account_id, region)
        enhanced_resource['console_link'] = console_link
        
        # Get cost estimate
        cost_estimate = get_resource_cost_estimate(resource)
        enhanced_resource['estimated_monthly_cost'] = cost_estimate
        
        enhanced.append(enhanced_resource)
    
    return enhanced

def generate_resource_arn(resource, account_id, region):
    """Generate ARN for resource"""
    
    service_map = {
        'AWS::S3::Bucket': f"arn:aws:s3:::{resource['name']}",
        'AWS::DynamoDB::Table': f"arn:aws:dynamodb:{region}:{account_id}:table/{resource['name']}",
        'AWS::Lambda::Function': f"arn:aws:lambda:{region}:{account_id}:function:{resource['name']}",
        'AWS::RDS::DBCluster': f"arn:aws:rds:{region}:{account_id}:cluster:{resource['name']}",
        'AWS::EC2::Instance': f"arn:aws:ec2:{region}:{account_id}:instance/{resource['name']}",
        'AWS::SecretsManager::Secret': f"arn:aws:secretsmanager:{region}:{account_id}:secret:{resource['name']}",
        'AWS::SNS::Topic': f"arn:aws:sns:{region}:{account_id}:{resource['name']}",
        'AWS::IAM::Role': f"arn:aws:iam::{account_id}:role/{resource['name']}"
    }
    
    return service_map.get(resource['type'], f"arn:aws:{resource['service']}:{region}:{account_id}:resource/{resource['name']}")

def generate_console_link(resource, account_id, region):
    """Generate AWS Console link for resource"""
    
    base_url = f"https://{region}.console.aws.amazon.com"
    
    link_map = {
        'AWS::S3::Bucket': f"{base_url}/s3/buckets/{resource['name']}",
        'AWS::DynamoDB::Table': f"{base_url}/dynamodbv2/home?region={region}#table?name={resource['name']}",
        'AWS::Lambda::Function': f"{base_url}/lambda/home?region={region}#/functions/{resource['name']}",
        'AWS::RDS::DBCluster': f"{base_url}/rds/home?region={region}#database:id={resource['name']}",
        'AWS::EC2::Instance': f"{base_url}/ec2/home?region={region}#InstanceDetails:instanceId={resource['name']}",
        'AWS::SecretsManager::Secret': f"{base_url}/secretsmanager/home?region={region}#/secret?name={quote(resource['name'])}",
        'AWS::SNS::Topic': f"{base_url}/sns/v3/home?region={region}#/topic/{quote(f'arn:aws:sns:{region}:{account_id}:{resource['name']}')}",
        'AWS::IAM::Role': f"https://console.aws.amazon.com/iam/home#/roles/{resource['name']}"
    }
    
    return link_map.get(resource['type'], f"{base_url}/console/home?region={region}")

def get_resource_cost_estimate(resource):
    """Get estimated monthly cost for resource"""
    
    cost_estimates = {
        'AWS::S3::Bucket': '$0.50 - $5.00',
        'AWS::DynamoDB::Table': '$1.00 - $10.00',
        'AWS::Lambda::Function': '$0.10 - $2.00',
        'AWS::RDS::DBCluster': '$50.00 - $200.00',
        'AWS::EC2::Instance': '$10.00 - $100.00',
        'AWS::SecretsManager::Secret': '$0.40',
        'AWS::SNS::Topic': '$0.01 - $1.00',
        'AWS::IAM::Role': '$0.00'
    }
    
    return cost_estimates.get(resource['type'], '$0.00 - $1.00')

def get_detailed_cost_analysis():
    """Get detailed cost analysis"""
    
    try:
        ce = boto3.client('ce')
        
        # Get last 30 days cost
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': (datetime.utcnow().replace(day=1)).strftime('%Y-%m-%d'),
                'End': datetime.utcnow().strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'}
            ]
        )
        
        costs = []
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                amount = float(group['Metrics']['BlendedCost']['Amount'])
                if amount > 0:
                    costs.append({
                        'service': service,
                        'amount': amount,
                        'currency': group['Metrics']['BlendedCost']['Unit']
                    })
        
        # Sort by cost descending
        costs.sort(key=lambda x: x['amount'], reverse=True)
        
        total_cost = sum(c['amount'] for c in costs)
        
        return {
            'total_monthly_cost': total_cost,
            'currency': 'USD',
            'top_services': costs[:10],
            'cost_trend': 'stable'  # Could be enhanced with historical data
        }
        
    except Exception as e:
        print(f"⚠️ Could not get cost analysis: {e}")
        return {
            'total_monthly_cost': 0,
            'currency': 'USD',
            'top_services': [],
            'cost_trend': 'unknown'
        }

def generate_console_links(account_id, region):
    """Generate useful AWS Console links"""
    
    return {
        'cost_explorer': f"https://console.aws.amazon.com/cost-management/home?region={region}#/cost-explorer",
        'cloudformation': f"https://{region}.console.aws.amazon.com/cloudformation/home?region={region}#/stacks",
        'cloudwatch': f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}",
        'iam': "https://console.aws.amazon.com/iam/home#/home",
        'billing': "https://console.aws.amazon.com/billing/home#/",
        'support': "https://console.aws.amazon.com/support/home#/"
    }

def generate_recommendations(validation_data):
    """Generate recommendations based on validation data"""
    
    recommendations = []
    
    resources = validation_data.get('resources', [])
    failed_resources = [r for r in resources if r['status'] == 'Failed']
    
    if failed_resources:
        recommendations.append({
            'type': 'critical',
            'title': 'Fix Failed Resources',
            'description': f"{len(failed_resources)} resources are in Failed state",
            'action': 'Review and redeploy failed resources'
        })
    
    # Check for missing encryption
    unencrypted = [r for r in resources if r['type'] in ['AWS::S3::Bucket', 'AWS::RDS::DBCluster'] and 'encryption' not in str(r.get('properties', {})).lower()]
    if unencrypted:
        recommendations.append({
            'type': 'security',
            'title': 'Enable Encryption',
            'description': f"{len(unencrypted)} resources may not have encryption enabled",
            'action': 'Review and enable encryption for sensitive resources'
        })
    
    # Cost optimization
    expensive_resources = [r for r in resources if r['type'] == 'AWS::RDS::DBCluster']
    if expensive_resources:
        recommendations.append({
            'type': 'cost',
            'title': 'Review Database Sizing',
            'description': f"{len(expensive_resources)} database clusters detected",
            'action': 'Review instance sizes and consider right-sizing'
        })
    
    return recommendations

def generate_html_report(report):
    """Generate HTML report for better visualization"""
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>IaL Enhanced Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background: #e8f4fd; padding: 15px; border-radius: 5px; text-align: center; }}
        .resources {{ margin: 20px 0; }}
        .resource {{ background: #f9f9f9; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .status-created {{ color: green; }}
        .status-failed {{ color: red; }}
        .console-link {{ color: #0066cc; text-decoration: none; }}
        .recommendations {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏗️ IaL Enhanced Validation Report</h1>
        <p><strong>Generated:</strong> {report['timestamp']}</p>
        <p><strong>Account:</strong> {report['account_id']} | <strong>Region:</strong> {report['region']}</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>{report['summary'].get('total_resources', 0)}</h3>
            <p>Total Resources</p>
        </div>
        <div class="metric">
            <h3>{report['summary'].get('created_resources', 0)}</h3>
            <p>Created</p>
        </div>
        <div class="metric">
            <h3>${report['cost_analysis'].get('total_monthly_cost', 0):.2f}</h3>
            <p>Monthly Cost</p>
        </div>
    </div>
    
    <h2>📋 Resources</h2>
    <div class="resources">
"""
    
    for resource in report['resources'][:20]:  # Limit to first 20
        status_class = f"status-{resource['status'].lower()}"
        html_content += f"""
        <div class="resource">
            <strong>{resource['name']}</strong> ({resource['type']})
            <span class="{status_class}">● {resource['status']}</span>
            <br>
            <small>
                ARN: {resource['arn']}<br>
                Cost: {resource['estimated_monthly_cost']} | 
                <a href="{resource['console_link']}" class="console-link" target="_blank">View in Console</a>
            </small>
        </div>
"""
    
    html_content += """
    </div>
    
    <h2>💡 Recommendations</h2>
    <div class="recommendations">
"""
    
    for rec in report['recommendations']:
        html_content += f"""
        <div>
            <strong>{rec['title']}</strong> ({rec['type']})<br>
            {rec['description']}<br>
            <em>Action: {rec['action']}</em>
        </div>
        <br>
"""
    
    html_content += """
    </div>
</body>
</html>
"""
    
    with open('reports/enhanced_validation_report.html', 'w') as f:
        f.write(html_content)
    
    print("📄 HTML report generated: reports/enhanced_validation_report.html")

def display_enhanced_summary(report):
    """Display enhanced summary to console"""
    
    print("\n" + "="*60)
    print("📊 ENHANCED VALIDATION REPORT SUMMARY")
    print("="*60)
    
    print(f"🏗️ Account: {report['account_id']} | Region: {report['region']}")
    print(f"⏰ Generated: {report['timestamp']}")
    print()
    
    summary = report['summary']
    print(f"📋 Resources: {summary.get('total_resources', 0)} total")
    print(f"✅ Created: {summary.get('created_resources', 0)}")
    print(f"🔍 Verified: {summary.get('verified_resources', 0)}")
    print(f"❌ Failed: {summary.get('failed_resources', 0)}")
    print()
    
    cost = report['cost_analysis']
    print(f"💰 Monthly Cost: ${cost.get('total_monthly_cost', 0):.2f} {cost.get('currency', 'USD')}")
    print()
    
    print("🔗 Quick Links:")
    links = report['console_links']
    print(f"   Cost Explorer: {links['cost_explorer']}")
    print(f"   CloudFormation: {links['cloudformation']}")
    print(f"   CloudWatch: {links['cloudwatch']}")
    print()
    
    if report['recommendations']:
        print("💡 Recommendations:")
        for rec in report['recommendations'][:3]:
            print(f"   • {rec['title']}: {rec['description']}")
    
    print("\n📄 Detailed reports saved to:")
    print("   • reports/enhanced_validation_report.json")
    print("   • reports/enhanced_validation_report.html")
    print("="*60)

def main():
    """Main function"""
    
    try:
        report = generate_enhanced_report()
        return 0 if report['summary'].get('failed_resources', 0) == 0 else 1
    except Exception as e:
        print(f"❌ Error generating enhanced report: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
