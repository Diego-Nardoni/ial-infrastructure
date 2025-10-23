#!/usr/bin/env python3
import boto3
import json
from datetime import datetime

dynamodb = boto3.client('dynamodb')
bedrock = boto3.client('bedrock-runtime')
sns = boto3.client('sns')

def detect_drift():
    response = dynamodb.query(
        TableName='mcp-provisioning-checklist',
        KeyConditionExpression='Project = :p',
        ExpressionAttributeValues={':p': {'S': 'mcp-spring-boot'}}
    )
    
    drifts = []
    for item in response.get('Items', []):
        resource_name = item['ResourceName']['S']
        if resource_name == 'DEPLOYMENT_LOCK':
            continue
        
        desired = json.loads(item.get('DesiredState', {}).get('S', '{}'))
        current = get_aws_state(resource_name)
        
        if desired != current:
            severity = classify_severity(resource_name, desired, current)
            drifts.append({
                'resource': resource_name,
                'severity': severity,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            dynamodb.update_item(
                TableName='mcp-provisioning-checklist',
                Key={'Project': {'S': 'mcp-spring-boot'}, 'ResourceName': {'S': resource_name}},
                UpdateExpression='SET DriftDetected = :d, DriftSeverity = :s',
                ExpressionAttributeValues={':d': {'BOOL': True}, ':s': {'S': severity}}
            )
    
    if drifts:
        print(f"🚨 Detected {len(drifts)} drifts")
        notify_drifts(drifts)
    else:
        print("✅ No drifts detected")

def get_aws_state(resource_name):
    return {}

def classify_severity(resource_name, desired, current):
    prompt = f"""Classify drift severity (CRITICAL/HIGH/MEDIUM/LOW):
Resource: {resource_name}
Desired: {json.dumps(desired)}
Current: {json.dumps(current)}"""
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 10,
            'messages': [{'role': 'user', 'content': prompt}]
        })
    )
    return json.loads(response['body'].read())['content'][0]['text'].strip()

def notify_drifts(drifts):
    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:ACCOUNT:alerts-critical',
        Subject=f'Drift Detected: {len(drifts)} resources',
        Message=json.dumps(drifts, indent=2)
    )

if __name__ == '__main__':
    detect_drift()
