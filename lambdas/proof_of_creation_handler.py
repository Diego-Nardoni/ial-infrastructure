#!/usr/bin/env python3
"""
Lambda Handler: Proof of Creation (Audit)
"""

import json
import boto3
from datetime import datetime


def handler(event, context):
    """
    Salva prova determinística de criação no DynamoDB
    
    Input:
        {
            "deployment_result": {
                "stack_id": "arn:...",
                "stack_name": "ial-ecs-cache"
            }
        }
    
    Output:
        {
            "proof_id": "uuid",
            "verified": true,
            "timestamp": "2025-11-13T20:00:00Z"
        }
    """
    
    # Extrair body do Payload (Step Functions invoke retorna Payload)
    deployment_payload = event['deployment_result']['Payload']
    deployment = deployment_payload.get('body', deployment_payload)
    
    # Verificar stack existe
    cfn = boto3.client('cloudformation')
    
    try:
        stack = cfn.describe_stacks(StackName=deployment['stack_name'])['Stacks'][0]
        
        # Listar recursos criados
        resources = cfn.list_stack_resources(StackName=deployment['stack_name'])
        
        # Salvar proof no DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('ial-resource-catalog')
        
        proof_id = f"proof-{deployment['stack_name']}-{int(datetime.now().timestamp())}"
        
        table.put_item(Item={
            'proof_id': proof_id,
            'stack_id': deployment['stack_id'],
            'stack_name': deployment['stack_name'],
            'stack_status': stack['StackStatus'],
            'resources_created': len(resources['StackResourceSummaries']),
            'created_at': datetime.now().isoformat(),
            'verified': True,
            'audit_trail': json.dumps({
                'pipeline': 'nl-intent',
                'execution_arn': context.invoked_function_arn
            })
        })
        
        return {
            "statusCode": 200,
            "body": {
                "proof_id": proof_id,
                "verified": True,
                "timestamp": datetime.now().isoformat(),
                "resources_count": len(resources['StackResourceSummaries'])
            }
        }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {
                "verified": False,
                "error": str(e)
            }
        }
