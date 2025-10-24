#!/usr/bin/env python3
"""Universal Resource Tracker - 90% Coverage"""

import boto3
import json
import re
import os
import yaml
import subprocess
from datetime import datetime
from pathlib import Path

dynamodb = boto3.client('dynamodb')

# Universal service to phase mapping
SERVICE_PHASE_MAP = {
    's3': '08-s3-storage',
    'ec2': '09-ec2-instances', 
    'rds': '11-rds-database',
    'dynamodb': '12-dynamodb-tables',
    'lambda': '13-lambda-functions',
    'stepfunctions': '14-step-functions',
    'sns': '15-sns-topics',
    'sqs': '16-sqs-queues',
    'iam': '05-iam-roles',
    'ecs': '08-ecs-services',
    'elasticloadbalancing': '10-load-balancers',
    'elasticloadbalancingv2': '10-load-balancers',
    'apigateway': '17-api-gateway',
    'cloudformation': '18-cloudformation',
    'route53': '19-route53',
    'cloudfront': '20-cloudfront',
    'elasticache': '21-elasticache',
    'elasticsearch': '22-elasticsearch',
    'kinesis': '23-kinesis',
    'firehose': '23-kinesis',
    'glue': '24-glue',
    'athena': '25-athena',
    'redshift': '26-redshift',
    'emr': '27-emr',
    'batch': '28-batch',
    'efs': '29-efs',
    'fsx': '29-efs',
    'backup': '30-backup',
    'kms': '01-kms-security',
    'secretsmanager': '04-secrets',
    'ssm': '04-parameter-store'
}

def track_universal_command(command):
    """Universal tracking for any AWS CLI command"""
    
    print(f"🔍 Universal tracking: {command}")
    
    # Parse command universally
    resource_info = parse_universal_aws_command(command)
    
    if resource_info:
        print(f"📝 Detected: {resource_info['name']} ({resource_info['type']})")
        
        # Register in DynamoDB
        register_resource(resource_info)
        
        # Add to phase
        add_to_phase_universal(resource_info)
        
        # Git commit
        auto_commit_universal(resource_info)
        
        print(f"✅ Universally tracked: {resource_info['name']}")
    else:
        print("⚠️ Command not recognized for tracking")

def parse_universal_aws_command(command):
    """Universal parser for AWS CLI commands"""
    
    # Extract service and operation
    aws_pattern = r'aws\s+([a-z0-9-]+)\s+([a-z0-9-]+)'
    match = re.search(aws_pattern, command)
    
    if not match:
        return None
    
    service = match.group(1)
    operation = match.group(2)
    
    # Check if it's a creation operation
    creation_ops = [
        'create-', 'run-', 'put-', 'make-', 'register-', 
        'deploy-', 'launch-', 'start-', 'build-', 'mb'
    ]
    
    is_creation = any(operation.startswith(op) for op in creation_ops)
    
    if not is_creation:
        return None
    
    # Extract resource name/identifier
    resource_name = extract_resource_name(command, service, operation)
    
    if not resource_name:
        return None
    
    # Map to CloudFormation type
    cf_type = map_to_cloudformation_type(service, operation)
    
    # Get phase
    phase = SERVICE_PHASE_MAP.get(service, f'99-{service}-resources')
    
    return {
        'name': resource_name,
        'type': cf_type,
        'service': service,
        'operation': operation,
        'phase': phase,
        'properties': extract_properties(command, service, operation)
    }

def extract_resource_name(command, service, operation):
    """Extract resource name from command"""
    
    # Common patterns for resource names
    patterns = [
        # --name parameter
        r'--(?:name|function-name|topic-name|queue-name|db-instance-identifier|cluster-name|service-name|state-machine-name)\s+([^\s]+)',
        # --table-name
        r'--table-name\s+([^\s]+)',
        # --role-name  
        r'--role-name\s+([^\s]+)',
        # --bucket-name or s3://bucket
        r'--bucket-name\s+([^\s]+)|s3://([^/\s]+)',
        # --group-name
        r'--group-name\s+([^\s]+)',
        # Last argument (fallback)
        r'\s+([a-zA-Z0-9][a-zA-Z0-9._-]+)(?:\s|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, command)
        if match:
            # Return first non-empty group
            for group in match.groups():
                if group:
                    return group
    
    # Generate name if not found
    return f"{service}-resource-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

def map_to_cloudformation_type(service, operation):
    """Map service/operation to CloudFormation type"""
    
    type_map = {
        's3': 'AWS::S3::Bucket',
        'ec2': {
            'run-instances': 'AWS::EC2::Instance',
            'create-security-group': 'AWS::EC2::SecurityGroup',
            'create-vpc': 'AWS::EC2::VPC',
            'create-subnet': 'AWS::EC2::Subnet'
        },
        'rds': 'AWS::RDS::DBInstance',
        'dynamodb': 'AWS::DynamoDB::Table',
        'lambda': 'AWS::Lambda::Function',
        'stepfunctions': 'AWS::StepFunctions::StateMachine',
        'sns': 'AWS::SNS::Topic',
        'sqs': 'AWS::SQS::Queue',
        'iam': {
            'create-role': 'AWS::IAM::Role',
            'create-user': 'AWS::IAM::User',
            'create-group': 'AWS::IAM::Group'
        },
        'ecs': {
            'create-cluster': 'AWS::ECS::Cluster',
            'create-service': 'AWS::ECS::Service'
        },
        'elasticloadbalancingv2': 'AWS::ElasticLoadBalancingV2::LoadBalancer',
        'apigateway': 'AWS::ApiGateway::RestApi',
        'kms': 'AWS::KMS::Key'
    }
    
    service_types = type_map.get(service)
    
    if isinstance(service_types, dict):
        return service_types.get(operation, f'AWS::{service.title()}::Resource')
    elif service_types:
        return service_types
    else:
        return f'AWS::{service.title()}::Resource'

def extract_properties(command, service, operation):
    """Extract properties from command"""
    
    properties = {}
    
    # Common property patterns
    prop_patterns = {
        'InstanceType': r'--instance-type\s+([^\s]+)',
        'ImageId': r'--image-id\s+([^\s]+)',
        'DBInstanceClass': r'--db-instance-class\s+([^\s]+)',
        'Engine': r'--engine\s+([^\s]+)',
        'Runtime': r'--runtime\s+([^\s]+)',
        'Handler': r'--handler\s+([^\s]+)',
        'Role': r'--role\s+(arn:aws:iam::[^\s]+)',
        'VpcId': r'--vpc-id\s+([^\s]+)',
        'SubnetId': r'--subnet-id\s+([^\s]+)'
    }
    
    for prop, pattern in prop_patterns.items():
        match = re.search(pattern, command)
        if match:
            properties[prop] = match.group(1)
    
    return properties

def register_resource(resource_info):
    """Register resource in DynamoDB"""
    
    try:
        dynamodb.put_item(
            TableName='mcp-provisioning-checklist',
            Item={
                'Project': {'S': 'ial'},
                'ResourceName': {'S': resource_info['name']},
                'Status': {'S': 'Created'},
                'ResourceType': {'S': resource_info['type']},
                'Phase': {'S': resource_info['phase']},
                'Properties': {'S': json.dumps(resource_info['properties'])},
                'CreatedVia': {'S': 'universal-tracker'},
                'Service': {'S': resource_info['service']},
                'Operation': {'S': resource_info['operation']},
                'Timestamp': {'S': datetime.utcnow().isoformat()}
            }
        )
        print(f"✅ Registered in DynamoDB: {resource_info['name']}")
        
    except Exception as e:
        print(f"❌ DynamoDB registration failed: {e}")

def add_to_phase_universal(resource_info):
    """Add resource to phase file"""
    
    phase_file = f"/home/ial/phases/{resource_info['phase']}.yaml"
    
    try:
        # Load or create phase
        if os.path.exists(phase_file):
            with open(phase_file, 'r') as f:
                phase_data = yaml.safe_load(f) or {}
        else:
            phase_data = {
                'phase_name': f"Universal {resource_info['service'].title()} Resources",
                'description': f"Auto-generated phase for {resource_info['service']} resources",
                'resource_count': 0,
                'Resources': {}
            }
        
        # Ensure Resources section
        if 'Resources' not in phase_data:
            phase_data['Resources'] = {}
        
        # Generate resource key
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', resource_info['name']).title()
        resource_key = f"Universal{clean_name}"
        
        # Add resource
        phase_data['Resources'][resource_key] = {
            'Type': resource_info['type'],
            'Properties': resource_info['properties'],
            'Metadata': {
                'CreatedVia': 'universal-tracker',
                'Service': resource_info['service'],
                'Operation': resource_info['operation'],
                'Timestamp': datetime.utcnow().isoformat(),
                'OriginalName': resource_info['name']
            }
        }
        
        # Update count
        phase_data['resource_count'] = len(phase_data['Resources'])
        
        # Save phase
        os.makedirs(os.path.dirname(phase_file), exist_ok=True)
        with open(phase_file, 'w') as f:
            yaml.dump(phase_data, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Added to phase {resource_info['phase']}: {resource_key}")
        
    except Exception as e:
        print(f"❌ Phase update failed: {e}")

def auto_commit_universal(resource_info):
    """Auto-commit resource to Git"""
    
    try:
        # Git add
        subprocess.run(['git', 'add', f"phases/{resource_info['phase']}.yaml"], 
                      cwd='/home/ial', check=True)
        
        # Git commit
        commit_msg = f"Universal-track: {resource_info['type']} {resource_info['name']}\n\nService: {resource_info['service']}\nOperation: {resource_info['operation']}\nPhase: {resource_info['phase']}"
        
        subprocess.run(['git', 'commit', '-m', commit_msg], 
                      cwd='/home/ial', check=True)
        
        print(f"✅ Git commit: {resource_info['name']}")
        
    except subprocess.CalledProcessError:
        print("⚠️ Git commit skipped (no changes or error)")
    except Exception as e:
        print(f"❌ Git error: {e}")

def discover_untracked_resources():
    """Discover existing resources via AWS APIs"""
    
    print("🔍 Discovering untracked resources via APIs...")
    
    tracked = get_tracked_resource_names()
    discovered = []
    
    # S3 Buckets
    try:
        s3 = boto3.client('s3')
        buckets = s3.list_buckets()
        for bucket in buckets.get('Buckets', []):
            name = bucket['Name']
            if name not in tracked:
                discovered.append({
                    'name': name,
                    'type': 'AWS::S3::Bucket',
                    'service': 's3',
                    'operation': 'create-bucket',
                    'phase': '08-s3-storage',
                    'properties': {'BucketName': name}
                })
    except Exception as e:
        print(f"⚠️ S3 discovery error: {e}")
    
    # DynamoDB Tables
    try:
        ddb = boto3.client('dynamodb')
        tables = ddb.list_tables()
        for table_name in tables.get('TableNames', []):
            if table_name not in tracked:
                discovered.append({
                    'name': table_name,
                    'type': 'AWS::DynamoDB::Table',
                    'service': 'dynamodb',
                    'operation': 'create-table',
                    'phase': '12-dynamodb-tables',
                    'properties': {'TableName': table_name}
                })
    except Exception as e:
        print(f"⚠️ DynamoDB discovery error: {e}")
    
    # Lambda Functions
    try:
        lambda_client = boto3.client('lambda')
        functions = lambda_client.list_functions()
        for func in functions.get('Functions', []):
            name = func['FunctionName']
            if name not in tracked:
                discovered.append({
                    'name': name,
                    'type': 'AWS::Lambda::Function',
                    'service': 'lambda',
                    'operation': 'create-function',
                    'phase': '13-lambda-functions',
                    'properties': {
                        'FunctionName': name,
                        'Runtime': func.get('Runtime', 'unknown')
                    }
                })
    except Exception as e:
        print(f"⚠️ Lambda discovery error: {e}")
    
    # SNS Topics
    try:
        sns = boto3.client('sns')
        topics = sns.list_topics()
        for topic in topics.get('Topics', []):
            arn = topic['TopicArn']
            name = arn.split(':')[-1]
            if name not in tracked:
                discovered.append({
                    'name': name,
                    'type': 'AWS::SNS::Topic',
                    'service': 'sns',
                    'operation': 'create-topic',
                    'phase': '15-sns-topics',
                    'properties': {'TopicName': name}
                })
    except Exception as e:
        print(f"⚠️ SNS discovery error: {e}")
    
    print(f"📊 Discovered {len(discovered)} untracked resources")
    
    # Track discovered resources
    for resource in discovered:
        print(f"📝 Auto-tracking discovered: {resource['name']}")
        register_resource(resource)
        add_to_phase_universal(resource)
    
    # Bulk commit
    if discovered:
        try:
            subprocess.run(['git', 'add', 'phases/'], cwd='/home/ial', check=True)
            subprocess.run(['git', 'commit', '-m', f'Universal-discovery: {len(discovered)} resources'], 
                          cwd='/home/ial', check=True)
            print(f"✅ Bulk committed {len(discovered)} discoveries")
        except:
            print("⚠️ Bulk commit failed")
    
    return discovered

def get_tracked_resource_names():
    """Get set of already tracked resource names"""
    
    try:
        response = dynamodb.query(
            TableName='mcp-provisioning-checklist',
            KeyConditionExpression='#proj = :p',
            ExpressionAttributeNames={'#proj': 'Project'},
            ExpressionAttributeValues={':p': {'S': 'ial'}}
        )
        
        tracked = set()
        for item in response.get('Items', []):
            tracked.add(item['ResourceName']['S'])
        
        return tracked
        
    except Exception as e:
        print(f"❌ Error getting tracked resources: {e}")
        return set()

def main():
    """Main function"""
    
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--discover':
            discover_untracked_resources()
        else:
            command = ' '.join(sys.argv[1:])
            track_universal_command(command)
    else:
        print("Usage:")
        print("  python3 universal-resource-tracker.py --discover")
        print("  python3 universal-resource-tracker.py aws stepfunctions create-state-machine --name MyStateMachine")

if __name__ == "__main__":
    main()
