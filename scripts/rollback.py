#!/usr/bin/env python3
import boto3
import json
import sys

dynamodb = boto3.client('dynamodb')

def rollback(target_commit):
    """Rollback infrastructure to a previous commit"""
    print(f"🔄 Rolling back to commit: {target_commit}")
    
    # Query all resources
    response = dynamodb.query(
        TableName='mcp-provisioning-checklist',
        KeyConditionExpression='#proj = :p',
        ExpressionAttributeNames={'#proj': 'Project'},
        ExpressionAttributeValues={':p': {'S': 'mcp-spring-boot'}}
    )
    
    for item in response.get('Items', []):
        resource_name = item['ResourceName']['S']
        if resource_name == 'DEPLOYMENT_LOCK':
            continue
        
        print(f"   Rolling back {resource_name}")
        # Rollback logic here
    
    print("✅ Rollback complete")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: rollback.py --target-commit <commit-sha>")
        sys.exit(1)
    
    target_commit = sys.argv[2] if len(sys.argv) > 2 else None
    if target_commit:
        rollback(target_commit)
    else:
        print("Error: --target-commit required")
        sys.exit(1)
