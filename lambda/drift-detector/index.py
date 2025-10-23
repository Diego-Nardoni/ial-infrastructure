import json
import boto3
from datetime import datetime

dynamodb = boto3.client('dynamodb')
bedrock = boto3.client('bedrock-runtime')
sns = boto3.client('sns')

def lambda_handler(event, context):
    resources = get_all_resources()
    drifts = []
    
    for resource in resources:
        drift = detect_drift(resource)
        if drift:
            drift['severity'] = classify_severity(drift)
            drifts.append(drift)
    
    if drifts:
        notify_email(drifts)
        store_drifts(drifts)
    
    return {'statusCode': 200, 'drifts': len(drifts)}

def get_all_resources():
    response = dynamodb.query(
        TableName='mcp-provisioning-checklist',
        KeyConditionExpression='Project = :p',
        ExpressionAttributeValues={':p': {'S': 'mcp-spring-boot'}}
    )
    return response.get('Items', [])

def detect_drift(resource):
    desired = json.loads(resource.get('DesiredState', {}).get('S', '{}'))
    current = get_aws_state(resource['ResourceName']['S'])
    
    if desired != current:
        return {
            'resource': resource['ResourceName']['S'],
            'desired': desired,
            'current': current,
            'timestamp': datetime.utcnow().isoformat()
        }
    return None

def get_aws_state(resource_name):
    # Simplified - real implementation would query AWS APIs
    return {}

def classify_severity(drift):
    prompt = f"""Classify drift severity:
Resource: {drift['resource']}
Changes: {json.dumps(drift['current'])}

Return: CRITICAL, HIGH, MEDIUM, or LOW"""
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({'anthropic_version': 'bedrock-2023-05-31', 
                        'max_tokens': 10, 'messages': [{'role': 'user', 'content': prompt}]})
    )
    return json.loads(response['body'].read())['content'][0]['text'].strip()

def notify_email(drifts):
    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:ACCOUNT:alerts-critical',
        Subject=f'Drift Detected: {len(drifts)} resources',
        Message=json.dumps(drifts, indent=2)
    )

def store_drifts(drifts):
    for drift in drifts:
        dynamodb.update_item(
            TableName='mcp-provisioning-checklist',
            Key={'Project': {'S': 'mcp-spring-boot'}, 'ResourceName': {'S': drift['resource']}},
            UpdateExpression='SET DriftDetected = :d, DriftSeverity = :s',
            ExpressionAttributeValues={':d': {'BOOL': True}, ':s': {'S': drift['severity']}}
        )
