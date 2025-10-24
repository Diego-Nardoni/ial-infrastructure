import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.client('dynamodb')

def lambda_handler(event, context):
    """Process CloudTrail events for resource tracking"""
    
    print(f"Processing CloudTrail event: {json.dumps(event)}")
    
    try:
        # Parse EventBridge event
        detail = event.get('detail', {})
        
        if not detail:
            print("No detail in event")
            return {'statusCode': 200}
        
        # Extract event info
        event_name = detail.get('eventName', '')
        event_source = detail.get('eventSource', '')
        aws_region = detail.get('awsRegion', 'us-east-1')
        
        # Check if it's a creation event
        if not is_creation_event(event_name):
            print(f"Not a creation event: {event_name}")
            return {'statusCode': 200}
        
        # Extract resource info
        resource_info = extract_resource_from_event(detail)
        
        if not resource_info:
            print(f"Could not extract resource from event: {event_name}")
            return {'statusCode': 200}
        
        # Check if already tracked
        if is_already_tracked(resource_info['name']):
            print(f"Resource already tracked: {resource_info['name']}")
            return {'statusCode': 200}
        
        # Track the resource
        track_cloudtrail_resource(resource_info, detail)
        
        print(f"✅ Tracked CloudTrail resource: {resource_info['name']}")
        
        return {'statusCode': 200, 'tracked': resource_info['name']}
        
    except Exception as e:
        print(f"❌ Error processing CloudTrail event: {str(e)}")
        return {'statusCode': 500, 'error': str(e)}

def is_creation_event(event_name):
    """Check if event represents resource creation"""
    
    creation_events = [
        'CreateBucket', 'CreateTable', 'CreateFunction', 'CreateTopic',
        'CreateQueue', 'CreateStateMachine', 'CreateRole', 'CreateUser',
        'CreateGroup', 'CreateCluster', 'CreateService', 'CreateDBInstance',
        'RunInstances', 'CreateSecurityGroup', 'CreateVpc', 'CreateSubnet',
        'CreateLoadBalancer', 'CreateTargetGroup', 'CreateRestApi',
        'CreateKey', 'CreateSecret', 'CreateParameter', 'CreateStack',
        'CreateDistribution', 'CreateCacheCluster', 'CreateReplicationGroup'
    ]
    
    return any(event_name.startswith(event) for event in creation_events)

def extract_resource_from_event(detail):
    """Extract resource information from CloudTrail event"""
    
    event_name = detail.get('eventName', '')
    event_source = detail.get('eventSource', '')
    request_params = detail.get('requestParameters', {})
    response_elements = detail.get('responseElements', {})
    
    # Map event source to service
    service = event_source.replace('.amazonaws.com', '').replace('aws-', '')
    
    # Extract resource name based on event type
    resource_name = None
    resource_type = None
    properties = {}
    
    # S3 Bucket
    if event_name == 'CreateBucket':
        resource_name = request_params.get('bucketName')
        resource_type = 'AWS::S3::Bucket'
        properties = {'BucketName': resource_name}
    
    # DynamoDB Table
    elif event_name == 'CreateTable':
        resource_name = request_params.get('tableName')
        resource_type = 'AWS::DynamoDB::Table'
        properties = {'TableName': resource_name}
    
    # Lambda Function
    elif event_name == 'CreateFunction':
        resource_name = request_params.get('functionName')
        resource_type = 'AWS::Lambda::Function'
        properties = {
            'FunctionName': resource_name,
            'Runtime': request_params.get('runtime')
        }
    
    # SNS Topic
    elif event_name == 'CreateTopic':
        resource_name = request_params.get('name')
        resource_type = 'AWS::SNS::Topic'
        properties = {'TopicName': resource_name}
    
    # SQS Queue
    elif event_name == 'CreateQueue':
        resource_name = request_params.get('queueName')
        resource_type = 'AWS::SQS::Queue'
        properties = {'QueueName': resource_name}
    
    # Step Functions State Machine
    elif event_name == 'CreateStateMachine':
        resource_name = request_params.get('name')
        resource_type = 'AWS::StepFunctions::StateMachine'
        properties = {'StateMachineName': resource_name}
    
    # IAM Role
    elif event_name == 'CreateRole':
        resource_name = request_params.get('roleName')
        resource_type = 'AWS::IAM::Role'
        properties = {'RoleName': resource_name}
    
    # EC2 Instance
    elif event_name == 'RunInstances':
        instances = response_elements.get('instancesSet', {}).get('items', [])
        if instances:
            resource_name = instances[0].get('instanceId')
            resource_type = 'AWS::EC2::Instance'
            properties = {
                'InstanceId': resource_name,
                'InstanceType': request_params.get('instanceType')
            }
    
    # RDS Instance
    elif event_name == 'CreateDBInstance':
        resource_name = request_params.get('dBInstanceIdentifier')
        resource_type = 'AWS::RDS::DBInstance'
        properties = {'DBInstanceIdentifier': resource_name}
    
    # Security Group
    elif event_name == 'CreateSecurityGroup':
        resource_name = response_elements.get('groupId')
        resource_type = 'AWS::EC2::SecurityGroup'
        properties = {
            'GroupId': resource_name,
            'GroupName': request_params.get('groupName')
        }
    
    if not resource_name:
        return None
    
    # Map service to phase
    service_phase_map = {
        's3': '08-s3-storage',
        'dynamodb': '12-dynamodb-tables',
        'lambda': '13-lambda-functions',
        'sns': '15-sns-topics',
        'sqs': '16-sqs-queues',
        'states': '14-step-functions',
        'iam': '05-iam-roles',
        'ec2': '09-ec2-instances',
        'rds': '11-rds-database'
    }
    
    phase = service_phase_map.get(service, f'99-{service}-resources')
    
    return {
        'name': resource_name,
        'type': resource_type,
        'service': service,
        'phase': phase,
        'properties': properties
    }

def is_already_tracked(resource_name):
    """Check if resource is already tracked in DynamoDB"""
    
    try:
        response = dynamodb.get_item(
            TableName='mcp-provisioning-checklist',
            Key={
                'Project': {'S': 'ial'},
                'ResourceName': {'S': resource_name}
            }
        )
        
        return 'Item' in response
        
    except Exception as e:
        print(f"Error checking if tracked: {e}")
        return False

def track_cloudtrail_resource(resource_info, event_detail):
    """Track resource discovered via CloudTrail"""
    
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
                'CreatedVia': {'S': 'cloudtrail-monitor'},
                'Service': {'S': resource_info['service']},
                'EventName': {'S': event_detail.get('eventName', '')},
                'EventSource': {'S': event_detail.get('eventSource', '')},
                'UserIdentity': {'S': json.dumps(event_detail.get('userIdentity', {}))},
                'Timestamp': {'S': datetime.utcnow().isoformat()}
            }
        )
        
        print(f"✅ CloudTrail resource tracked in DynamoDB: {resource_info['name']}")
        
        # Send notification
        send_discovery_notification(resource_info, event_detail)
        
    except Exception as e:
        print(f"❌ Error tracking CloudTrail resource: {e}")

def send_discovery_notification(resource_info, event_detail):
    """Send notification about discovered resource"""
    
    try:
        sns = boto3.client('sns')
        
        # Try to get topic ARN
        account_id = boto3.client('sts').get_caller_identity()['Account']
        region = os.environ.get('AWS_REGION', 'us-east-1')
        topic_arn = f"arn:aws:sns:{region}:{account_id}:ial-alerts-critical"
        
        user_identity = event_detail.get('userIdentity', {})
        user_name = user_identity.get('userName', user_identity.get('type', 'Unknown'))
        
        message = f"""🔍 CLOUDTRAIL AUTO-DISCOVERY
        
Resource: {resource_info['type']}
Name: {resource_info['name']}
Service: {resource_info['service']}
Phase: {resource_info['phase']}

Created by: {user_name}
Event: {event_detail.get('eventName', '')}
Source IP: {event_detail.get('sourceIPAddress', 'Unknown')}

✅ Automatically tracked in DynamoDB
✅ Will be added to phase file on next sync
        """
        
        sns.publish(
            TopicArn=topic_arn,
            Subject=f"Auto-Discovery: {resource_info['type']} {resource_info['name']}",
            Message=message.strip()
        )
        
        print("📧 Discovery notification sent")
        
    except Exception as e:
        print(f"⚠️ Could not send notification: {e}")
