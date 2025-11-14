#!/usr/bin/env python3
"""
Lambda Handler: Deploy CloudFormation Stack
"""

import json
import boto3


def handler(event, context):
    """
    Deploy CloudFormation stack após aprovação do PR
    
    Input:
        {
            "phase_result": {
                "phase_name": "ecs-cache",
                "yaml_content": "..."
            }
        }
    
    Output:
        {
            "stack_id": "arn:aws:cloudformation:...",
            "stack_name": "ial-ecs-cache",
            "status": "CREATE_IN_PROGRESS"
        }
    """
    
    # Extrair body do Payload (Step Functions invoke retorna Payload)
    phase_payload = event['phase_result']['Payload']
    phase_result = phase_payload.get('body', phase_payload)
    stack_name = f"ial-{phase_result['phase_name']}"
    
    cfn = boto3.client('cloudformation')
    
    # Deploy stack
    response = cfn.create_stack(
        StackName=stack_name,
        TemplateBody=phase_result['yaml_content'],
        Capabilities=['CAPABILITY_NAMED_IAM'],
        Tags=[
            {'Key': 'ManagedBy', 'Value': 'IAL'},
            {'Key': 'Pipeline', 'Value': 'NL-Intent'}
        ]
    )
    
    return {
        "statusCode": 200,
        "body": {
            "stack_id": response['StackId'],
            "stack_name": stack_name,
            "status": "CREATE_IN_PROGRESS"
        }
    }
