#!/usr/bin/env python3
"""Sync Resource Deletion to DynamoDB"""

import boto3
import json
import sys
import re
from datetime import datetime

dynamodb = boto3.client('dynamodb')

def sync_deletion(resource_name, resource_type=None):
    """Update DynamoDB when resource is deleted"""
    
    try:
        # Update resource status to Deleted
        dynamodb.update_item(
            TableName='mcp-provisioning-checklist',
            Key={
                'Project': {'S': 'ial'},
                'ResourceName': {'S': resource_name}
            },
            UpdateExpression='SET #status = :deleted, DeletedAt = :time',
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues={
                ':deleted': {'S': 'Deleted'},
                ':time': {'S': datetime.utcnow().isoformat()}
            }
        )
        
        print(f"✅ Synced deletion: {resource_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error syncing deletion for {resource_name}: {e}")
        return False

def detect_aws_deletions():
    """Detect resources deleted from AWS but still marked as Created in DynamoDB"""
    
    print("🔍 Detecting AWS deletions...")
    
    # Get all resources marked as Created
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
            ':status': {'S': 'Created'}
        }
    )
    
    deleted_count = 0
    
    for item in response.get('Items', []):
        resource_name = item['ResourceName']['S']
        resource_type = item.get('ResourceType', {}).get('S', 'Unknown')
        
        # Check if resource still exists in AWS
        if not resource_exists_in_aws(resource_name, resource_type):
            print(f"🗑️ Resource deleted from AWS: {resource_name}")
            sync_deletion(resource_name, resource_type)
            deleted_count += 1
    
    print(f"✅ Synced {deleted_count} deletions")
    return deleted_count

def resource_exists_in_aws(resource_name, resource_type):
    """Check if resource still exists in AWS"""
    
    try:
        if resource_type == 'AWS::S3::Bucket':
            s3 = boto3.client('s3')
            s3.head_bucket(Bucket=resource_name)
            return True
            
        elif resource_type == 'AWS::EC2::SecurityGroup':
            ec2 = boto3.client('ec2')
            response = ec2.describe_security_groups(GroupIds=[resource_name])
            return len(response['SecurityGroups']) > 0
            
        elif resource_type == 'AWS::ECS::Service':
            ecs = boto3.client('ecs')
            # Extract cluster and service name from resource_name
            if '/' in resource_name:
                cluster, service = resource_name.split('/', 1)
            else:
                cluster = 'default'
                service = resource_name
            response = ecs.describe_services(cluster=cluster, services=[service])
            return len(response['services']) > 0
            
        elif resource_type == 'AWS::RDS::DBInstance':
            rds = boto3.client('rds')
            response = rds.describe_db_instances(DBInstanceIdentifier=resource_name)
            return len(response['DBInstances']) > 0
            
        elif resource_type == 'AWS::ElasticLoadBalancingV2::LoadBalancer':
            elbv2 = boto3.client('elbv2')
            response = elbv2.describe_load_balancers(LoadBalancerArns=[resource_name])
            return len(response['LoadBalancers']) > 0
            
        else:
            # For unknown types, assume it exists (safer)
            return True
            
    except Exception:
        # If we can't check or get an error, assume it's deleted
        return False

def parse_aws_command(command):
    """Parse AWS CLI command to extract resource info for deletion tracking"""
    
    # S3 bucket deletion
    s3_delete = re.search(r'aws s3 rb s3://([^/\s]+)', command)
    if s3_delete:
        return s3_delete.group(1), 'AWS::S3::Bucket'
    
    # EC2 Security Group deletion
    sg_delete = re.search(r'aws ec2 delete-security-group.*--group-id\s+([sg-\w]+)', command)
    if sg_delete:
        return sg_delete.group(1), 'AWS::EC2::SecurityGroup'
    
    # ECS Service deletion
    ecs_delete = re.search(r'aws ecs delete-service.*--service\s+([^\s]+)', command)
    if ecs_delete:
        return ecs_delete.group(1), 'AWS::ECS::Service'
    
    # RDS Instance deletion
    rds_delete = re.search(r'aws rds delete-db-instance.*--db-instance-identifier\s+([^\s]+)', command)
    if rds_delete:
        return rds_delete.group(1), 'AWS::RDS::DBInstance'
    
    return None, None

def main():
    """Main function - can be called with command or run detection"""
    
    if len(sys.argv) > 1:
        # Called with AWS command - parse and sync
        command = ' '.join(sys.argv[1:])
        resource_name, resource_type = parse_aws_command(command)
        
        if resource_name:
            sync_deletion(resource_name, resource_type)
        else:
            print("⚠️ Could not parse resource from command")
    else:
        # Run detection mode
        detect_aws_deletions()

if __name__ == "__main__":
    main()
