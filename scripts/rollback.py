#!/usr/bin/env python3
import boto3
import argparse
import subprocess

dynamodb = boto3.client('dynamodb')

def rollback(target_commit):
    print(f"🔄 Rolling back to {target_commit}")
    
    result = subprocess.run(
        ['git', 'diff', target_commit, 'HEAD', '--', 'phases/'],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        print(f"Changes to rollback:\n{result.stdout}")
        
        response = dynamodb.query(
            TableName='mcp-provisioning-checklist',
            KeyConditionExpression='Project = :p',
            ExpressionAttributeValues={':p': {'S': 'mcp-spring-boot'}}
        )
        
        for item in response.get('Items', []):
            resource_name = item['ResourceName']['S']
            version = int(item.get('Version', {}).get('N', '0'))
            
            dynamodb.update_item(
                TableName='mcp-provisioning-checklist',
                Key={'Project': {'S': 'mcp-spring-boot'}, 'ResourceName': {'S': resource_name}},
                UpdateExpression='SET Version = :v',
                ExpressionAttributeValues={':v': {'N': str(version - 1)}}
            )
        
        print("✅ Rollback completed")
    else:
        print("❌ Rollback failed")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target-commit', required=True)
    args = parser.parse_args()
    rollback(args.target_commit)
